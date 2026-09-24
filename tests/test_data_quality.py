"""Corpus checks distinguish candidate output from publishable data."""

import json
import hashlib
from datetime import date
from pathlib import Path

from backend.ingestion.schema import Chunk
from backend.ingestion.temporal import eligibility
from backend.retrieval.graph_utils import get_supplementary_docs, is_valid


def test_candidate_corpus_schema_and_lineage():
    root = Path(__file__).resolve().parents[1]
    stage = root / "data/staging/phase1-candidate"
    sources = {item["source_id"] for item in json.loads((root / "data/registry/sources.json").read_text(encoding="utf-8"))}
    documents = {item["doc_id"] for item in json.loads((root / "data/registry/documents.json").read_text(encoding="utf-8"))}
    chunks = [Chunk.model_validate_json(line) for line in (stage / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    assert chunks
    assert len({item.chunk_id for item in chunks}) == len(chunks)
    assert all(item.doc_id in documents for item in chunks)
    assert all(ref.source_id in sources for item in chunks for ref in item.source_refs)
    assert all(item.verification_status == "pending" for item in chunks)
    manifest = json.loads((stage / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["chunks"] == len(chunks)
    assert manifest["published"] is False
    assert manifest["gate1"] == "PASS"


def test_source_bytes_and_required_coverage_are_intact():
    root = Path(__file__).resolve().parents[1]
    sources = json.loads((root / "data/registry/sources.json").read_text(encoding="utf-8"))
    assert all(hashlib.sha256((root / item["path"]).read_bytes()).hexdigest() == item["sha256"] for item in sources)
    coverage = json.loads((root / "data/registry/coverage.json").read_text(encoding="utf-8"))
    parsed = json.loads((root / "data/staging/phase1-candidate/parsed.json").read_text(encoding="utf-8"))
    assert all(item["source_present"] and f"doc:{item['doc_number']}" in parsed for item in coverage)
    assert [article["article_number"] for article in parsed["doc:51/2024/QH15"]["articles"]
            if article["content_kind"] == "normative" and len(article["structural_path"]) == 2] == ["1", "2", "3"]


def test_candidate_relations_never_change_validity():
    candidate = {"source_doc": "70/2023/NĐ-CP", "target_doc": "152/2020/NĐ-CP",
                 "relation_type": "thay_the", "scope": "toan_bo", "effective_date": "2023-09-18",
                 "review_status": "candidate"}
    assert is_valid("152/2020/NĐ-CP", "Điều 1", [candidate], "2024-01-01")
    assert get_supplementary_docs("152/2020/NĐ-CP", [candidate]) == []


def test_verified_relation_requires_effective_date_in_legacy_graph():
    relation = {"source_doc": "45/2019/QH14", "target_doc": "10/2012/QH13",
                "relation_type": "thay_the", "scope": "toan_bo", "review_status": "verified"}
    assert is_valid("10/2012/QH13", "Điều 1", [relation], "2022-01-01")
    relation["effective_date"] = "2021-01-01"
    assert is_valid("10/2012/QH13", "Điều 1", [relation], "2020-12-31")
    assert not is_valid("10/2012/QH13", "Điều 1", [relation], "2021-01-01")


def test_verified_v2_document_expiry_boundary():
    root = Path(__file__).resolve().parents[1]
    relations = json.loads((root / "data/registry/relations_verified.json").read_text(encoding="utf-8"))
    assert is_valid("74/2024/NĐ-CP", "Điều 3", relations, "2025-12-31")
    assert not is_valid("74/2024/NĐ-CP", "Điều 3", relations, "2026-01-01")


def test_temporal_interval_boundary_and_unknown():
    version = {"verification_status": "verified", "valid_from": "2021-01-01", "valid_to": "2025-07-01"}
    assert eligibility(version, date(2021, 1, 1), coverage_verified=True, applicability_resolved=True) == "eligible"
    assert eligibility(version, date(2025, 7, 1), coverage_verified=True, applicability_resolved=True) == "ineligible"
    assert eligibility(version, date(2022, 1, 1), coverage_verified=False, applicability_resolved=True) == "unknown"
    assert eligibility(version, date(2022, 1, 1), coverage_verified=True,
                       applicability_resolved=True, population_matches=None) == "unknown"
    assert eligibility(version, date(2022, 1, 1), coverage_verified=True,
                       applicability_resolved=True, population_matches=False) == "ineligible"
    assert eligibility(version, date(2022, 1, 1), coverage_verified=True,
                       applicability_resolved=True, transition_resolved=False) == "unknown"
