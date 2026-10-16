"""Offline v1.1 engineering checks; no semantic/legal or DOCX-render acceptance."""
from collections import Counter
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_legal_forms_v11 as builder
import export_legal_forms as exporter


def temporary_directory():
    base = ROOT / ".cache/legal-form-v11-tests"
    base.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=base)


def read_rows(path):
    return [exporter.strict_json(line) for line in path.read_text(encoding="utf-8").splitlines()]


class OfflineBoundaries(unittest.TestCase):
    def test_missing_raw_source_is_fatal(self):
        with temporary_directory() as tmp:
            records = [(1, b"", {"content_kind": "form", "source_refs": [{"source_id": "missing"}]})]
            sources = {"missing": {"path": "does-not-exist.docx", "sha256": "0" * 64}}
            with self.assertRaisesRegex(ValueError, "Referenced raw source missing"):
                exporter.make_audit(Path(tmp), sources, records, {})

    def test_ambiguous_selection_is_refused(self):
        with self.assertRaises(ValueError):
            builder.select_candidates([], doc_id="doc:one")
        with self.assertRaises(ValueError):
            builder.select_candidates([], doc_id="", provision_id="one")

    def test_incomplete_hit_cannot_be_deduplicated(self):
        with self.assertRaises(ValueError):
            builder.duplicate_context({"content_hash": "same"})

    def test_nested_missing_blank_or_wrong_type_provenance_is_rejected(self):
        original = read_rows(ROOT / "exports/legal_forms/v1/form_chunks.jsonl")[0]
        invalid_refs = [{}, {"source_id": "src:known"}, {"locator": "body/p:1"}]
        for field in ("source_id", "locator"):
            for value in (None, "", " \t\n", "\u00a0", 0, False, [], {}):
                ref = {"source_id": "src:known", "locator": "body/p:1"}
                ref[field] = value
                invalid_refs.append(ref)
        invalid_refs.append({"source_id": "", "locator": ""})
        for ref in invalid_refs:
            with self.subTest(ref=ref):
                left, right = deepcopy(original), deepcopy(original)
                left["chunk_id"], right["chunk_id"] = "repro:left", "repro:right"
                left["source_refs"], right["source_refs"] = [deepcopy(ref)], [deepcopy(ref)]
                before = deepcopy([left, right])
                with self.assertRaises(ValueError):
                    builder.duplicate_context(left)
                with self.assertRaises(ValueError):
                    builder.deduplicate_hits([left, right])
                self.assertEqual([left, right], before)

    def test_source_refs_must_be_a_nonempty_list(self):
        hit = read_rows(ROOT / "exports/legal_forms/v1/form_chunks.jsonl")[0]
        for refs in (None, [], {}, "source", ({"source_id": "src:known", "locator": "body/p:1"},)):
            with self.subTest(refs=refs):
                hit["source_refs"] = refs
                with self.assertRaises(ValueError):
                    builder.deduplicate_hits([hit, deepcopy(hit)])

    def test_every_source_ref_is_validated_even_after_a_valid_ref(self):
        hit = read_rows(ROOT / "exports/legal_forms/v1/form_chunks.jsonl")[0]
        valid = deepcopy(hit["source_refs"][0])
        for bad in ({}, None, "source", [], 7):
            for refs in ([valid, bad], [bad, valid]):
                with self.subTest(refs=refs):
                    hit["source_refs"] = refs
                    with self.assertRaises(ValueError):
                        builder.deduplicate_hits([hit, deepcopy(hit)])

    def test_complete_provenance_still_collapses_without_changing_input(self):
        left = read_rows(ROOT / "exports/legal_forms/v1/form_chunks.jsonl")[0]
        right = deepcopy(left)
        right["chunk_id"] = "repro:same-context"
        # Null source URLs are valid when source ID and locator are complete.
        for hit in (left, right):
            hit["source_refs"] = [{"source_id": "src:known", "locator": "body/p:1", "source_url": None}]
        before = deepcopy([left, right])
        groups = builder.deduplicate_hits([left, right])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["chunk_ids"], [left["chunk_id"], right["chunk_id"]])
        self.assertEqual([left, right], before)


@unittest.skipUnless(os.environ.get("LEGAL_FORM_SOURCE_REPO"), "Set LEGAL_FORM_SOURCE_REPO for real published snapshot checks")
class SnapshotV11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(os.environ["LEGAL_FORM_SOURCE_REPO"])
        cls.v1 = ROOT / "exports/legal_forms/v1"
        cls.v11 = ROOT / "exports/legal_forms/v1.1"
        cls.snapshot = exporter.read_snapshot(cls.source)
        cls.selected = [c for _, _, c in cls.snapshot[6] if c["content_kind"] in ("form", "annex")]
        cls.originals = {c["chunk_id"]: c for c in cls.selected}
        cls.manifest = json.loads((cls.v11 / "manifest.json").read_text(encoding="utf-8"))
        cls.overlays = read_rows(cls.v11 / "metadata_overlay.jsonl")
        cls.candidates = read_rows(cls.v11 / "template_candidates.jsonl")
        cls.groups = read_rows(cls.v11 / "fragment_groups.jsonl")

    def test_overlay_is_complete_and_unique(self):
        self.assertEqual(len(self.overlays), 343)
        self.assertEqual(Counter(c["chunk_id"] for c in self.overlays), Counter(self.originals.keys()))
        self.assertTrue(all(o["source_integrity"] == o["content_integrity"] == "MATCH" for o in self.overlays))

    def test_legal_metadata_flags_and_no_promotion(self):
        forms = [o for o in self.overlays if self.originals[o["chunk_id"]]["content_kind"] == "form"]
        self.assertEqual(sum("ISSUED_YEAR_DIFFERS_FROM_DOC_NUMBER" in o["legal_metadata_reasons"] for o in forms), 59)
        self.assertEqual(sum("REPEATED_BASELINE_VALID_FROM_REQUIRES_REVIEW" in o["legal_metadata_reasons"] for o in forms), 119)
        for o in self.overlays:
            self.assertEqual(o["legal_metadata_status"], "PENDING_REVIEW")
            self.assertEqual(o["structural_fidelity"], "TEXT_ONLY")
            self.assertFalse(o["generation_ready"])
            self.assertNotIn("valid_from", o)
            self.assertNotIn("valid_to", o)
            self.assertNotIn("issued_date", o)
            self.assertEqual(set(o["source_verification_statuses"].values()), {"pending"})
            self.assertEqual(o["original_chunk_verification_status"], "verified")

    def test_grouping_no_chunk_loss_duplication_or_order_change(self):
        members = []
        lines = {c["chunk_id"]: line for line, _, c in self.snapshot[6]}
        for group in self.groups:
            parts = group["parts"]
            self.assertEqual([p["part_index"] for p in parts], list(range(1, len(parts) + 1)))
            self.assertEqual([p["source_line_number"] for p in parts], sorted(lines[p["chunk_id"]] for p in parts))
            self.assertFalse(group["lossless_reassembly_verified"])
            for part in parts:
                c = self.originals[part["chunk_id"]]
                self.assertEqual(c["provision_id"], group["provision_id"])
                self.assertEqual(c["provision_version_id"], group["provision_version_id"])
                self.assertEqual(c["content_hash"], part["content_hash"])
                members.append(c["chunk_id"])
        self.assertEqual(Counter(members), Counter(self.originals.keys()))
        self.assertEqual(len(self.groups), 257)

    def test_annex_candidates_and_uncertainty_queue_are_separate(self):
        self.assertEqual(len(self.candidates), 208)
        annex = [c for c in self.candidates if c["content_kind"] == "annex"]
        self.assertEqual(len(annex), 23)
        self.assertTrue(all(c["template_candidate_type"] == "ANNEX_FORM_CANDIDATE" for c in annex))
        queue = read_rows(self.v11 / "annex_review_queue.jsonl")
        self.assertEqual(len(queue), 23)
        self.assertFalse({c["group_id"] for c in queue} & {c["group_id"] for c in self.candidates})
        self.assertTrue(all(c["review_status"] == "NEEDS_REVIEW" for c in queue))
        for c in annex:
            for p in c["parts"]:
                self.assertEqual(self.originals[p["chunk_id"]]["content_kind"], "annex")

    def test_exact_selection_keeps_document_path_and_source_scope(self):
        for candidate in self.candidates:
            rows = builder.select_candidates(self.candidates, doc_id=candidate["doc_id"],
                provision_id=candidate["provision_id"], structural_path=candidate["structural_path"], source_id=candidate["source_ids"][0])
            self.assertIn(candidate, rows)
            self.assertTrue(all(r["doc_id"] == candidate["doc_id"] and r["structural_path"] == candidate["structural_path"] for r in rows))
        first = self.candidates[0]
        self.assertEqual(builder.select_candidates(self.candidates, doc_id="doc:absent", provision_id=first["provision_id"]), [])
        self.assertEqual(builder.select_candidates(self.candidates, doc_id=first["doc_id"], provision_id=first["provision_id"], source_id="src:absent"), [])

    def test_same_hash_never_merges_distinct_sources_or_versions(self):
        c = deepcopy(self.selected[0])
        same = deepcopy(c)
        same["chunk_id"] = "fixture-same-context"
        source = deepcopy(c)
        source["chunk_id"] = "fixture-other-source"
        source["source_refs"][0]["source_id"] = "fixture-other-source"
        version = deepcopy(c)
        version["chunk_id"] = "fixture-other-version"
        version["provision_version_id"] += ":other"
        locator = deepcopy(c)
        locator["chunk_id"] = "fixture-other-locator"
        locator["source_refs"][0]["locator"] += ":other"
        groups = builder.deduplicate_hits([c, same, source, version, locator])
        self.assertEqual(len(groups), 4)
        self.assertEqual(groups[0]["chunk_ids"], [c["chunk_id"], same["chunk_id"]])
        self.assertEqual(builder.deduplicate_hits([c, c])[0]["chunk_ids"], [c["chunk_id"]])

    def test_duplicate_hash_inventory_does_not_collapse_cross_context(self):
        rows = read_rows(self.v11 / "duplicate_content_groups.jsonl")
        expected = Counter(c["content_hash"] for c in self.selected)
        self.assertEqual({r["content_hash"] for r in rows}, {h for h, n in expected.items() if n > 1})
        for row in rows:
            self.assertFalse(row["cross_context_collapse_allowed"])
            for ids in row["safe_context_groups"]:
                self.assertEqual(len({builder.duplicate_context(self.originals[cid]) for cid in ids}), 1)

    def test_docx_alternatives_are_original_registry_records_unverified(self):
        candidates = json.loads((self.v11 / "docx_mapping_candidates.json").read_text(encoding="utf-8"))
        self.assertFalse(candidates["mapping_verified"])
        self.assertEqual(candidates["alternative_source_integrity"], "NOT_CHECKED")
        for entries in candidates["documents"].values():
            for source in entries:
                self.assertEqual(source, self.snapshot[4][source["source_id"]])
                self.assertEqual(source["format"], "docx")
        for o in self.overlays:
            c = self.originals[o["chunk_id"]]
            direct = any(self.snapshot[4][sid]["format"] == "docx" for sid in builder.source_ids(c))
            self.assertEqual(o["docx_mapping_status"] == "DIRECT", direct)
            if o["docx_mapping_status"] == "UNVERIFIED_ALTERNATIVE":
                self.assertTrue(o["docx_alternative_source_ids"])
                self.assertEqual(o["docx_alternative_integrity"], "NOT_CHECKED")

    def test_all_generated_files_including_readme_have_checksums(self):
        seen = set()
        for line in (self.v11 / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
            expected, name = line.split("  ", 1)
            self.assertEqual(exporter.sha((self.v11 / name).read_bytes()), expected)
            seen.add(name)
        self.assertEqual(seen, {p.name for p in self.v11.iterdir() if p.is_file()} - {"SHA256SUMS.txt"})
        self.assertIn("README.md", seen)

    def test_missing_raw_source_refuses_export_before_any_output(self):
        # A fake repo root is used; the real raw source is never renamed or removed.
        c = self.selected[0]
        with temporary_directory() as tmp:
            repo = Path(tmp) / "repo"
            release = repo / "data/releases" / self.snapshot[2]["release_id"]
            inputs = {
                exporter.CHUNKS: builder.jsonl([c]),
                exporter.SOURCES: exporter.json_bytes([self.snapshot[4][sid] for sid in builder.source_ids(c)]),
                exporter.DOCUMENTS: exporter.json_bytes([self.snapshot[5][c["doc_id"]]]),
            }
            for name, data in inputs.items():
                path = release / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            manifest = {"release_id": self.snapshot[2]["release_id"], "published": True, "chunks": 1,
                "snapshot_file_sha256": {name: exporter.sha(data) for name, data in inputs.items()}}
            manifest_data = exporter.json_bytes(manifest)
            (release / "manifest.json").write_bytes(manifest_data)
            (repo / "data/active_release.json").write_bytes(exporter.json_bytes({"release_id": manifest["release_id"],
                "path": release.relative_to(repo).as_posix(), "manifest_sha256": exporter.sha(manifest_data)}))
            output = Path(tmp) / "output"
            with self.assertRaisesRegex(ValueError, "Referenced raw source missing"):
                exporter.export(repo, output, self.manifest["export_timestamp"], ROOT)
            self.assertFalse(output.exists())

    def test_immutable_v1_and_snapshot_unchanged(self):
        exporter.unchanged(self.snapshot[7])
        _, pins = builder.verified_v1(self.v1)
        exporter.unchanged(pins)
        self.assertEqual(self.manifest["v1_file_sha256"], {p.relative_to(self.v1).as_posix(): h for p, h in pins.items()})

    def test_v11_replay_covers_all_artifacts_and_is_idempotent(self):
        with temporary_directory() as tmp:
            output = Path(tmp) / "replay"
            for _ in range(2):
                builder.build(self.source, self.v1, output, self.manifest["export_timestamp"], self.manifest["build_base_commit"])
            self.assertEqual({p.name for p in output.iterdir()}, {p.name for p in self.v11.iterdir()})
            for path in output.iterdir():
                self.assertEqual(path.read_bytes(), (self.v11 / path.name).read_bytes())

    def test_corrupt_v1_and_overlapping_or_conflicting_output_refused(self):
        with temporary_directory() as tmp:
            bad = Path(tmp) / "bad"
            bad.mkdir()
            (bad / "SHA256SUMS.txt").write_text("0" * 64 + "  manifest.json\n", encoding="utf-8")
            (bad / "manifest.json").write_bytes(b"{}")
            with self.assertRaisesRegex(ValueError, "v1 package checksum mismatch"):
                builder.verified_v1(bad)
            with self.assertRaisesRegex(ValueError, "overlaps immutable"):
                builder.build(self.source, self.v1, self.v1, self.manifest["export_timestamp"])
            conflict = Path(tmp) / "conflict"
            conflict.mkdir()
            (conflict / "metadata_overlay.jsonl").write_bytes(b"owner data")
            with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
                builder.build(self.source, self.v1, conflict, self.manifest["export_timestamp"])
            self.assertEqual([p.name for p in conflict.iterdir()], ["metadata_overlay.jsonl"])


if __name__ == "__main__":
    unittest.main()
