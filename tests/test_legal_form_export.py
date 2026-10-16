"""Focused stdlib tests; no ingestion, embedding, network or legal acceptance."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("export_legal_forms", ROOT / "scripts/export_legal_forms.py")
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


def temporary_directory():
    base = ROOT / ".cache/legal-form-export-tests"
    base.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=base)


class BoundaryTests(unittest.TestCase):
    def test_strict_json_rejects_invalid_objects(self):
        for value in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '{"a":'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                exporter.strict_json(value)

    def test_path_traversal_rejected(self):
        with self.assertRaises(ValueError):
            exporter.inside(ROOT, "../outside")

    def test_ambiguous_annex_is_not_promoted_to_form(self):
        rows = [(1, b"", {"content": "Phụ lục\nMẫu số 01 | Tên mẫu\nMẫu số 02 | Tên mẫu khác"})]
        self.assertEqual(exporter.annex_category(rows)[0], "NEEDS_REVIEW")

    def test_protected_input_mutation_detected(self):
        with temporary_directory() as tmp:
            path = Path(tmp) / "source"
            path.write_bytes(b"original")
            pins = {path: exporter.sha(path.read_bytes())}
            path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "Protected source changed"):
                exporter.unchanged(pins)


@unittest.skipUnless(os.environ.get("LEGAL_FORM_SOURCE_REPO"), "Set LEGAL_FORM_SOURCE_REPO for actual snapshot checks")
class PublishedExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(os.environ["LEGAL_FORM_SOURCE_REPO"])
        cls.snapshot = exporter.read_snapshot(cls.source)
        cls.records = cls.snapshot[6]
        cls.output = ROOT / "exports/legal_forms/v1"
        cls.manifest = json.loads((cls.output / "manifest.json").read_text(encoding="utf-8"))
        cls.audit = json.loads((cls.output / "audit.json").read_text(encoding="utf-8"))

    def exported(self, kind):
        return [exporter.strict_json(line) for line in (self.output / f"{kind}_chunks.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_counts_kinds_ids_and_valid_json(self):
        for kind in ("form", "annex"):
            rows = self.exported(kind)
            expected = [c for _, _, c in self.records if c["content_kind"] == kind]
            self.assertEqual(len(rows), len(expected))
            self.assertEqual(len(rows), self.manifest["totals"][kind]["chunks"])
            self.assertTrue(all(c["content_kind"] == kind for c in rows))
            self.assertEqual(len(rows), len({c["chunk_id"] for c in rows}))

    def test_original_bytes_and_every_field_preserved(self):
        for kind in ("form", "annex"):
            expected = b"".join(line for _, line, c in self.records if c["content_kind"] == kind)
            self.assertEqual((self.output / f"{kind}_chunks.jsonl").read_bytes(), expected)
            self.assertEqual(self.exported(kind), [c for _, _, c in self.records if c["content_kind"] == kind])

    def test_content_hash_and_legal_metadata_preserved(self):
        originals = {c["chunk_id"]: c for _, _, c in self.records}
        for kind in ("form", "annex"):
            for c in self.exported(kind):
                self.assertEqual(exporter.sha(c["content"].encode("utf-8")), c["content_hash"])
                for field in ("verification_status", "issued_date", "valid_from", "valid_to", "release_id", "source_refs", "structural_path"):
                    self.assertEqual(c[field], originals[c["chunk_id"]][field])

    def test_registry_subset_is_exact_and_complete(self):
        registry = json.loads((self.output / "source_registry.json").read_text(encoding="utf-8"))
        lookup = {s["source_id"]: s for s in registry}
        used = {r["source_id"] for kind in ("form", "annex") for c in self.exported(kind) for r in c["source_refs"]}
        self.assertEqual(set(lookup), used)
        for sid in used:
            self.assertEqual(lookup[sid], self.snapshot[4][sid])
        documents = json.loads((self.output / "document_registry.json").read_text(encoding="utf-8"))
        for doc in documents:
            self.assertEqual(doc, self.snapshot[5][doc["doc_id"]])

    def test_output_hashes(self):
        for name, info in self.manifest["files"].items():
            data = (self.output / name).read_bytes()
            self.assertEqual(exporter.sha(data), info["sha256"])
            self.assertEqual(len(data), info["bytes"])

    def test_all_provisions_and_fragment_order_in_inventory(self):
        inventory = {e["provision_id"]: e for e in self.audit["provision_inventory"]}
        for kind in ("form", "annex"):
            for c in self.exported(kind):
                self.assertIn(c["chunk_id"], inventory[c["provision_id"]]["chunk_ids_in_source_order"])
        for entry in inventory.values():
            self.assertEqual(entry["source_line_numbers"], sorted(entry["source_line_numbers"]))
        self.assertTrue(any(e["has_fragments"] and len(e["source_line_numbers"]) > 1 for e in inventory.values()))

    def test_table_samples_have_source_evidence_and_preserved_text(self):
        self.assertEqual(len(self.audit["table_samples"]), 3)
        lookup = {c["chunk_id"]: c for c in self.exported("form")}
        for sample in self.audit["table_samples"]:
            self.assertGreater(sample["docx_tables"], 0)
            self.assertGreater(sample["text_pipe_count"], 0)
            self.assertEqual(sample["finding"], "STRUCTURAL_FIDELITY_LIMITATION")
            self.assertTrue(lookup[sample["chunk_id"]]["is_fragment"])
        self.assertTrue(any(s["grid_spans"] and s["vertical_merges"] for s in self.audit["table_samples"]))

    def test_all_annexes_have_separate_classification(self):
        entries = [e for e in self.audit["provision_inventory"] if e["content_kind"] == "annex"]
        self.assertEqual(len(entries), self.manifest["totals"]["annex"]["unique_provision_ids"])
        allowed = {"FORM", "CATALOG", "APPLICATION_LIST", "OTHER_NORMATIVE_OR_REFERENCE", "NEEDS_REVIEW"}
        self.assertTrue(all(e["category"] in allowed and e["category_evidence"] for e in entries))
        self.assertTrue(any(e["category"] == "NEEDS_REVIEW" for e in entries))

    def test_source_release_and_raw_bytes_unchanged(self):
        exporter.unchanged(self.snapshot[7])
        for check in self.audit["raw_source_checks"]:
            self.assertEqual(check["status"], "MATCH")
            self.assertEqual(exporter.sha((self.source / check["path"]).read_bytes()), check["expected_sha256"])

    def test_two_replays_are_byte_identical_and_idempotent(self):
        pins = {"source_commit": self.manifest["source_repository_commit_sha"], "exporter_base_commit": self.manifest["exporter_base_commit_sha"]}
        with temporary_directory() as tmp:
            dirs = [Path(tmp) / "one", Path(tmp) / "two"]
            for out in dirs:
                exporter.export(self.source, out, self.manifest["export_timestamp"], ROOT, **pins)
            exporter.export(self.source, dirs[0], self.manifest["export_timestamp"], ROOT, **pins)
            for path in dirs[0].iterdir():
                self.assertEqual(path.read_bytes(), (dirs[1] / path.name).read_bytes())
                if path.name == "manifest.json":
                    # v1 is immutable: the hardened exporter now has a different code hash.
                    replay = json.loads(path.read_bytes())
                    self.assertEqual(replay.pop("exporter_sha256"), exporter.sha(Path(exporter.__file__).read_bytes()))
                    historical = dict(self.manifest)
                    historical.pop("exporter_sha256")
                    self.assertEqual(replay, historical)
                else:
                    self.assertEqual(path.read_bytes(), (self.output / path.name).read_bytes())

    def test_conflicting_output_refused_before_partial_write(self):
        with temporary_directory() as tmp:
            out = Path(tmp)
            (out / "form_chunks.jsonl").write_bytes(b"existing user file")
            with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
                exporter.export(self.source, out, self.manifest["export_timestamp"], ROOT)
            self.assertEqual(list(out.iterdir()), [out / "form_chunks.jsonl"])
            self.assertEqual((out / "form_chunks.jsonl").read_bytes(), b"existing user file")

    def test_output_under_source_data_rejected(self):
        with self.assertRaisesRegex(ValueError, "Output must not be"):
            exporter.export(self.source, self.source / "data/releases/export-forbidden", self.manifest["export_timestamp"], ROOT)

    def test_bad_pointer_hash_rejected(self):
        with temporary_directory() as tmp:
            fake = Path(tmp)
            release = fake / "data/releases/test"
            release.mkdir(parents=True)
            (release / "manifest.json").write_bytes(b"{}")
            (fake / "data/active_release.json").write_bytes(exporter.json_bytes({"release_id": "test", "path": "data/releases/test", "manifest_sha256": "0" * 64}))
            with self.assertRaisesRegex(ValueError, "Active manifest SHA256 mismatch"):
                exporter.read_snapshot(fake)


if __name__ == "__main__":
    unittest.main()
