import hashlib
import subprocess
import sys

import pytest
from pydantic import ValidationError

import scripts.review_decisions as reviews
import scripts.build_registry as build_registry
from backend.ingestion.schema import EvidenceRef, ReviewDependency
from scripts.review_decisions import (
    ReviewDecision,
    apply_coverage_decisions,
    apply_document_decisions,
    apply_source_decisions,
    canonical_hash,
    content_fingerprint,
    evidence_digest,
    input_hash,
)


def test_review_requires_evidence_and_reviewer():
    with pytest.raises(ValidationError):
        ReviewDecision.model_validate({
            "subject_type": "document", "subject_id": "doc:test", "review_type": "metadata",
            "input_sha256": "a" * 64, "conclusion": "verified", "evidence_source_id": "src:a",
            "evidence_locator": "", "reviewer": "", "reviewed_at": "2026-09-17"})


def test_rebuild_applies_only_hash_bound_metadata_decision(monkeypatch):
    sources = [{"source_id": "src:a", "sha256": "a" * 64}]
    document = {"doc_id": "doc:test", "source_ids": ["src:a"], "title": "test", "verification_status": "pending"}
    decision = {
        "subject_type": "document", "subject_id": "doc:test", "review_type": "metadata",
        "input_sha256": input_hash(document, {"src:a": sources[0]}),
        "conclusion": "verified", "evidence_source_id": "src:a", "evidence_locator": "article:1",
        "reviewer": "reviewer", "reviewed_at": "2026-09-17", "values": {
            "title": "reviewed title", "issued_date": "2020-12-14", "valid_from": "2021-02-01"},
    }
    monkeypatch.setattr(reviews, "load_decisions", lambda _: [ReviewDecision.model_validate(decision)])
    assert apply_document_decisions([document.copy()], sources, None)[0]["title"] == "reviewed title"
    changed = [{**sources[0], "sha256": hashlib.sha256(b"changed").hexdigest()}]
    stale = apply_document_decisions([document.copy()], changed, None)[0]
    assert stale["title"] == "test"
    assert stale["verification_status"] == "pending"


def test_stale_and_unsupported_decisions_have_diagnostics(monkeypatch):
    sources = [{"source_id": "src:a", "sha256": "a" * 64}]
    document = {"doc_id": "doc:test", "source_ids": ["src:a"], "verification_status": "pending"}
    base = {
        "subject_type": "document", "subject_id": "doc:test", "input_sha256": "b" * 64,
        "conclusion": "verified", "evidence_source_id": "src:a", "evidence_locator": "header",
        "reviewer": "reviewer", "reviewed_at": "2026-09-17", "values": {
            "title": "reviewed title", "issued_date": "2020-12-14", "valid_from": "2021-02-01",
        },
    }
    decisions = [
        ReviewDecision.model_validate({**base, "review_type": "metadata"}),
        ReviewDecision.model_validate({**base, "review_type": "identity"}),
    ]
    monkeypatch.setattr(reviews, "load_decisions", lambda _: decisions)
    diagnostics = []
    apply_document_decisions([document], sources, None, diagnostics=diagnostics)
    assert {row["code"] for row in diagnostics} == {"stale_input", "unsupported_review_type"}


def test_source_conflict_with_empty_first_values_is_rejected(monkeypatch):
    row = {"source_id": "src:a", "sha256": "a" * 64, "verification_status": "pending"}
    digest = input_hash(row, {"src:a": row})
    base = {
        "subject_type": "source", "subject_id": "src:a", "review_type": "identity",
        "input_sha256": digest, "conclusion": "verified", "evidence_source_id": "src:a",
        "evidence_locator": "bytes", "reviewer": "a", "reviewed_at": "2026-09-17",
    }
    decisions = [
        ReviewDecision.model_validate({**base, "values": {}}),
        ReviewDecision.model_validate({**base, "reviewer": "b", "values": {"role": "canonical"}}),
    ]
    monkeypatch.setattr(reviews, "load_decisions", lambda _: decisions)
    with pytest.raises(ValueError, match="Conflicting"):
        apply_source_decisions([row], None)


def test_retired_generator_imports_but_cli_always_fails():
    import scripts.retired_auto_metadata_review as retired

    assert callable(retired.main)
    result = subprocess.run(
        [sys.executable, "-m", "scripts.retired_auto_metadata_review"],
        text=True, capture_output=True, check=False,
    )
    assert result.returncode != 0
    assert "permanently disabled" in result.stderr


def _v2_evidence(source_id="src:a", source_hash="a" * 64, locator="page:1"):
    return [{
        "source_id": source_id,
        "source_sha256": source_hash,
        "full_content_sha256": source_hash,
        "locator": locator,
        "locator_sha256": canonical_hash("complete located text"),
    }]


def test_v2_decision_stales_when_final_locator_content_changes(monkeypatch):
    source = {"source_id": "src:a", "sha256": "a" * 64}
    document = {"doc_id": "doc:test", "source_ids": ["src:a"], "verification_status": "pending"}
    dependencies = {"fidelity:doc:test": "b" * 64}
    decision = ReviewDecision.model_validate({
        "decision_version": 2,
        "subject_type": "document",
        "subject_id": "doc:test",
        "review_type": "metadata",
        "input_fingerprint": content_fingerprint(document, {"src:a": source}, dependencies),
        "conclusion": "verified",
        "evidence": _v2_evidence(),
        "dependencies": [{"dependency_id": "fidelity:doc:test", "fingerprint": "b" * 64}],
        "reviewer": "independent-reviewer",
        "reviewed_at": "2026-09-23",
        "proposed_values": {"title": "draft"},
        "verified_values": {
            "title": "reviewed", "issued_date": "2020-01-01", "valid_from": "2021-01-01",
        },
    })
    monkeypatch.setattr(reviews, "load_decisions", lambda _: [decision])
    locator_key = "src:a#page:1"
    good = apply_document_decisions(
        [document.copy()], [source], None,
        dependency_fingerprints=dependencies,
        evidence_content_fingerprints={"src:a": "a" * 64},
        evidence_locator_fingerprints={locator_key: canonical_hash("complete located text")},
    )
    assert good[0]["verification_status"] == "verified"

    diagnostics = []
    stale = apply_document_decisions(
        [document.copy()], [source], None,
        diagnostics=diagnostics,
        dependency_fingerprints=dependencies,
        evidence_content_fingerprints={"src:a": "a" * 64},
        evidence_locator_fingerprints={locator_key: canonical_hash("same prefix, changed final paragraph")},
    )
    assert stale[0]["verification_status"] == "pending"
    assert diagnostics[0]["code"] == "stale_evidence_locator"


def test_metadata_decision_does_not_verify_coverage(monkeypatch):
    source = {"source_id": "src:a", "sha256": "a" * 64}
    coverage = {
        "topic": "labor", "doc_number": "45/2019/QH14", "target_as_of": "2026-09-17",
        "population": "general", "source_present": True, "verification_status": "pending", "gap": None,
    }
    metadata = ReviewDecision.model_validate({
        "subject_type": "document", "subject_id": "doc:45/2019/QH14", "review_type": "metadata",
        "input_sha256": "a" * 64, "conclusion": "verified", "evidence_source_id": "src:a",
        "evidence_locator": "header", "reviewer": "reviewer", "reviewed_at": "2026-09-23",
        "values": {"title": "T", "issued_date": "2019-01-01", "valid_from": "2020-01-01"},
    })
    monkeypatch.setattr(reviews, "load_decisions", lambda _: [metadata])
    result = apply_coverage_decisions([coverage.copy()], [source], None)
    assert result[0]["verification_status"] == "pending"


def test_evidence_digest_is_stable_and_not_self_referential():
    evidence = _v2_evidence()
    first = evidence_digest(evidence)
    envelope = {"evidence_digest": first, "candidate_id": "candidate-x"}
    assert evidence_digest(evidence) == first
    assert evidence_digest(evidence) != canonical_hash(envelope)


def test_v2_verified_review_requires_dependency():
    with pytest.raises(ValidationError, match="typed dependencies"):
        ReviewDecision.model_validate({
            "decision_version": 2,
            "subject_type": "document",
            "subject_id": "doc:test",
            "review_type": "metadata",
            "input_fingerprint": "b" * 64,
            "conclusion": "verified",
            "evidence": _v2_evidence(),
            "reviewer": "reviewer",
            "reviewed_at": "2026-09-23",
            "verified_values": {
                "title": "T", "issued_date": "2025-01-01", "valid_from": "2025-01-01",
            },
        })


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (EvidenceRef, {
            "source_id": "src:a",
            "source_sha256": "a" * 64,
            "full_content_sha256": "a" * 64,
            "locator": "   ",
            "locator_sha256": "b" * 64,
        }),
        (ReviewDependency, {"dependency_id": "   ", "fingerprint": "b" * 64}),
    ],
)
def test_v2_binding_identifiers_reject_blank_strings(model, payload):
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_rejected_v2_metadata_does_not_apply_verified_values(monkeypatch):
    source = {"source_id": "src:a", "sha256": "a" * 64}
    document = {
        "doc_id": "doc:test", "source_ids": ["src:a"], "title": "original",
        "issued_date": None, "valid_from": None, "verification_status": "pending",
    }
    dependencies = {"source-identity:src:a": "b" * 64}
    decision = ReviewDecision.model_validate({
        "decision_version": 2,
        "subject_type": "document",
        "subject_id": "doc:test",
        "review_type": "metadata",
        "input_fingerprint": content_fingerprint(document, {"src:a": source}, dependencies),
        "conclusion": "rejected",
        "evidence": _v2_evidence(),
        "dependencies": [{"dependency_id": "source-identity:src:a", "fingerprint": "b" * 64}],
        "reviewer": "reviewer",
        "reviewed_at": "2026-09-24",
        "verified_values": {
            "title": "must not apply", "issued_date": "2025-01-01", "valid_from": "2025-01-01",
        },
    })
    monkeypatch.setattr(reviews, "load_decisions", lambda _: [decision])
    result = apply_document_decisions(
        [document.copy()], [source], None,
        dependency_fingerprints=dependencies,
        evidence_content_fingerprints={"src:a": "a" * 64},
        evidence_locator_fingerprints={
            "src:a#page:1": canonical_hash("complete located text"),
        },
    )[0]
    assert result["verification_status"] == "rejected"
    assert result["title"] == "original"
    assert result["issued_date"] is None
    assert result["valid_from"] is None


def test_content_fingerprint_rejects_missing_subject_source():
    subject = {"doc_id": "doc:test", "source_ids": ["src:a", "src:missing"]}
    with pytest.raises(KeyError, match="src:missing"):
        content_fingerprint(subject, {"src:a": {"sha256": "a" * 64}}, {})


def test_v2_application_diagnoses_missing_subject_source(monkeypatch):
    source = {"source_id": "src:a", "sha256": "a" * 64}
    complete = {"doc_id": "doc:test", "source_ids": ["src:a"], "verification_status": "pending"}
    dependencies = {"source-identity:src:a": "b" * 64}
    decision = ReviewDecision.model_validate({
        "decision_version": 2,
        "subject_type": "document",
        "subject_id": "doc:test",
        "review_type": "metadata",
        "input_fingerprint": content_fingerprint(complete, {"src:a": source}, dependencies),
        "conclusion": "verified",
        "evidence": _v2_evidence(),
        "dependencies": [{"dependency_id": "source-identity:src:a", "fingerprint": "b" * 64}],
        "reviewer": "reviewer",
        "reviewed_at": "2026-09-23",
        "verified_values": {
            "title": "T", "issued_date": "2025-01-01", "valid_from": "2025-01-01",
        },
    })
    monkeypatch.setattr(reviews, "load_decisions", lambda _: [decision])
    diagnostics = []
    missing = {**complete, "source_ids": ["src:a", "src:missing"]}
    result = apply_document_decisions(
        [missing], [source], None,
        diagnostics=diagnostics,
        dependency_fingerprints=dependencies,
        evidence_content_fingerprints={"src:a": "a" * 64},
        evidence_locator_fingerprints={
            "src:a#page:1": canonical_hash("complete located text"),
        },
    )
    assert result[0]["verification_status"] == "pending"
    assert diagnostics[0]["code"] == "missing_subject_source"


def test_v2_review_requires_independent_full_content_binding(monkeypatch):
    source = {"source_id": "src:a", "sha256": "a" * 64}
    document = {"doc_id": "doc:test", "source_ids": ["src:a"], "verification_status": "pending"}
    dependencies = {"source-identity:src:a": "b" * 64}
    decision = ReviewDecision.model_validate({
        "decision_version": 2,
        "subject_type": "document",
        "subject_id": "doc:test",
        "review_type": "metadata",
        "input_fingerprint": content_fingerprint(document, {"src:a": source}, dependencies),
        "conclusion": "verified",
        "evidence": _v2_evidence(),
        "dependencies": [{"dependency_id": "source-identity:src:a", "fingerprint": "b" * 64}],
        "reviewer": "reviewer",
        "reviewed_at": "2026-09-23",
        "verified_values": {
            "title": "T", "issued_date": "2025-01-01", "valid_from": "2025-01-01",
        },
    })
    monkeypatch.setattr(reviews, "load_decisions", lambda _: [decision])
    diagnostics = []
    result = apply_document_decisions(
        [document.copy()], [source], None,
        diagnostics=diagnostics,
        dependency_fingerprints=dependencies,
        evidence_content_fingerprints={"src:a": "c" * 64},
        evidence_locator_fingerprints={
            "src:a#page:1": canonical_hash("complete located text"),
        },
    )
    assert result[0]["verification_status"] == "pending"
    assert diagnostics[0]["code"] == "stale_evidence_content"


def test_registry_production_path_passes_v2_binding_index(monkeypatch):
    source = {"source_id": "src:a", "sha256": "a" * 64, "verification_status": "pending"}
    document = {"doc_id": "doc:test", "source_ids": ["src:a"], "verification_status": "pending"}
    coverage = []
    dependencies = {"source-identity:src:a": "b" * 64}
    decision = ReviewDecision.model_validate({
        "decision_version": 2,
        "subject_type": "document",
        "subject_id": "doc:test",
        "review_type": "metadata",
        "input_fingerprint": content_fingerprint(document, {"src:a": source}, dependencies),
        "conclusion": "verified",
        "evidence": _v2_evidence(),
        "dependencies": [{"dependency_id": "source-identity:src:a", "fingerprint": "b" * 64}],
        "reviewer": "reviewer",
        "reviewed_at": "2026-09-23",
        "verified_values": {
            "title": "T", "issued_date": "2025-01-01", "valid_from": "2025-01-01",
        },
    })
    monkeypatch.setattr(reviews, "load_decisions", lambda _: [decision])
    monkeypatch.setattr(build_registry, "load_review_bindings", lambda _: reviews.ReviewBindingIndex(
        source_full_content_sha256={"src:a": "a" * 64},
        locator_sha256={"src:a#page:1": canonical_hash("complete located text")},
        dependency_fingerprints=dependencies,
    ))
    _, documents, _ = build_registry.apply_registry_reviews(
        [source], [document], coverage,
        reviews_dir=None, bindings_path=None,
    )
    assert documents[0]["verification_status"] == "verified"
