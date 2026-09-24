from backend.ingestion.chunker_v2 import chunk_articles, chunk_versions
from backend.ingestion.parser import parse_legal_document
import pytest


def test_split_chunk_refs_only_its_source_lines():
    blocks = [
        {"kind": "paragraph", "text": "Điều 1. Phạm vi", "locator": "p:1"},
        {"kind": "paragraph", "text": "1. Nội dung khoản một đủ dài để tách chunk.", "locator": "p:2"},
        {"kind": "paragraph", "text": "2. Nội dung khoản hai đủ dài để tách chunk.", "locator": "p:3"},
    ]
    parsed = parse_legal_document("", {
        "doc_id": "doc:test", "doc_number": "1/2025/QH15", "doc_title": "Test",
        "doc_type": "luat", "issued_date": None, "valid_from": None,
    }, blocks)
    chunks = chunk_articles(parsed, release_id="test", source_id="src:test",
                            source_url=None, max_chars=65)
    assert len(chunks) == 3
    assert [ref["locator"] for ref in chunks[0]["source_refs"]] == ["p:1"]
    assert [ref["locator"] for ref in chunks[1]["source_refs"]] == ["p:2"]
    assert [ref["locator"] for ref in chunks[2]["source_refs"]] == ["p:3"]


def test_chunk_versions_raises_on_missing_source_refs():
    """Regression: chunk_versions must raise a ValueError when a version
    carries no source_refs.

    Previously this branch silently fabricated a source_id from
    structural_path (e.g. 'article:1'), which is never a valid registry
    source_id. The invariant is: any version reaching chunk_versions MUST
    have valid source_refs populated. A version with source_refs=[] causes
    _parts() to produce a synthetic empty-string locator ('') that has no
    match in loc_to_refs, triggering the contract violation.
    """
    parsed = {
        "doc:test": parse_legal_document("", {
            "doc_id": "doc:test", "doc_number": "1/TEST", "doc_title": "T",
            "doc_type": "luat", "issued_date": None, "valid_from": None,
        }, [{"kind": "paragraph", "text": "Điều 1. Nội dung.", "locator": "p:1"}])
    }
    # A version with source_refs=[] — simulates a materialised version whose
    # provenance was stripped or never populated.  chunk_versions must refuse
    # to produce a chunk rather than fabricate a source_id.
    bad_version = {
        "provision_id": "doc:test:body/article:1",
        "provision_version_id": "doc:test:body/article:1@deadbeef12345678",
        "doc_id": "doc:test",
        "structural_path": ["body", "article:1"],
        "content_kind": "normative",
        "content": "Điều 1. Nội dung.",
        "source_refs": [],          # Empty: no provenance
        "applied_relation_ids": [],
        "valid_from": None,
        "valid_to": None,
        "proposed_valid_from": None,
        "proposed_valid_to": None,
        "verification_status": "pending",
    }
    with pytest.raises(ValueError, match="Data-contract violation"):
        chunk_versions([bad_version], parsed, release_id="test-release")
