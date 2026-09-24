"""Materialize signed decisions only while their exact inputs are unchanged.

Decisions live outside generated registry files. A rebuild may refresh facts but it
must not erase a review or silently carry it across changed source bytes.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from backend.ingestion.schema import EvidenceRef, ReviewBindingIndex, ReviewDecision


MUTABLE_REVIEW_FIELDS = {
    "verification_status", "review_status", "reviewed_by", "reviewed_at", "gap",
}


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def content_fingerprint(
    subject: dict, sources: dict[str, dict], dependency_fingerprints: dict[str, str] | None = None,
) -> str:
    """Hash every semantic input while excluding only mutable review outputs."""
    stable_subject = {key: value for key, value in subject.items() if key not in MUTABLE_REVIEW_FIELDS}
    source_ids = subject.get("source_ids", [])
    if "source_id" in subject:
        source_ids = [subject["source_id"]]
    raw = {
        "subject": stable_subject,
        "sources": [
            {"source_id": source_id, "sha256": sources[source_id]["sha256"]}
            for source_id in sorted(source_ids)
        ],
        "dependencies": sorted((dependency_fingerprints or {}).items()),
    }
    return canonical_hash(raw)


def evidence_digest(evidence: list[EvidenceRef | dict]) -> str:
    """Digest evidence payload only; the digest field itself is never an input."""
    normalized = [
        item.model_dump(mode="json", exclude_none=True) if isinstance(item, EvidenceRef) else item
        for item in evidence
    ]
    return canonical_hash(normalized)


def load_review_bindings(path: Path) -> ReviewBindingIndex:
    if not path.exists():
        return ReviewBindingIndex()
    try:
        return ReviewBindingIndex.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"Invalid review binding index {path}: {error}") from error


def input_hash(subject: dict, sources: dict[str, dict]) -> str:
    if "source_id" in subject:
        raw = {"source_id": subject["source_id"], "sha256": subject["sha256"]}
    else:
        raw = {"doc_id": subject["doc_id"], "source_hashes": sorted(
            (sid, sources[sid]["sha256"]) for sid in subject["source_ids"])}
    return hashlib.sha256(json.dumps(raw, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def load_decisions(directory: Path) -> list[ReviewDecision]:
    """Load all review decisions from *directory*, excluding the archive/ subdirectory."""
    if not directory.exists():
        return []
    decisions = []
    for path in sorted(directory.glob("*.json")):
        try:
            decisions.append(ReviewDecision.model_validate(json.loads(path.read_text(encoding="utf-8"))))
        except (json.JSONDecodeError, ValueError) as error:
            raise ValueError(f"Invalid review decision {path}: {error}") from error
    return decisions


def _diagnose(diagnostics: list[dict] | None, code: str, decision: ReviewDecision) -> None:
    if diagnostics is not None:
        diagnostics.append({
            "code": code,
            "subject_type": decision.subject_type,
            "subject_id": decision.subject_id,
            "review_type": decision.review_type,
            "input_fingerprint": decision.input_fingerprint or decision.input_sha256,
        })


def _matches(
    decision: ReviewDecision, subject: dict, sources: dict[str, dict],
    dependency_fingerprints: dict[str, str] | None,
    evidence_content_fingerprints: dict[str, str] | None,
    evidence_locator_fingerprints: dict[str, str] | None,
    diagnostics: list[dict] | None,
) -> bool:
    if decision.decision_version == 1:
        matches = input_hash(subject, sources) == decision.input_sha256
    else:
        current_dependencies = dependency_fingerprints or {}
        bound_dependencies: dict[str, str] = {}
        for dependency in decision.dependencies:
            if current_dependencies.get(dependency.dependency_id) != dependency.fingerprint:
                _diagnose(diagnostics, "stale_dependency", decision)
                return False
            bound_dependencies[dependency.dependency_id] = dependency.fingerprint
        try:
            current_fingerprint = content_fingerprint(subject, sources, bound_dependencies)
        except KeyError:
            _diagnose(diagnostics, "missing_subject_source", decision)
            return False
        matches = current_fingerprint == decision.input_fingerprint
        if matches:
            for evidence in decision.evidence:
                source = sources.get(evidence.source_id)
                if not source:
                    _diagnose(diagnostics, "missing_evidence_source", decision)
                    return False
                if source.get("sha256") != evidence.source_sha256:
                    _diagnose(diagnostics, "stale_evidence", decision)
                    return False
                if (evidence_content_fingerprints or {}).get(evidence.source_id) != evidence.full_content_sha256:
                    _diagnose(diagnostics, "stale_evidence_content", decision)
                    return False
                locator_key = f"{evidence.source_id}#{evidence.locator}"
                if (evidence_locator_fingerprints or {}).get(locator_key) != evidence.locator_sha256:
                    _diagnose(diagnostics, "stale_evidence_locator", decision)
                    return False
    if not matches:
        _diagnose(diagnostics, "stale_input", decision)
    return matches


def _evidence_source_ids(decision: ReviewDecision) -> set[str]:
    if decision.decision_version == 1:
        return {decision.evidence_source_id} if decision.evidence_source_id else set()
    return {item.source_id for item in decision.evidence}


def _conflict_error(subject_id: str, review_type: str, decisions: list[ReviewDecision]) -> str:
    summaries = "; ".join(
        f"{d.reviewer}@{d.reviewed_at}:{json.dumps(d.applied_values(), ensure_ascii=False)}"
        for d in decisions
    )
    return (
        f"Conflicting review decisions for {subject_id!r} (review_type={review_type!r}): "
        f"{len(decisions)} decisions with distinct outcomes — {summaries}. "
        "Resolve conflict before rebuilding registry."
    )


def apply_source_decisions(
    rows: list[dict], directory: Path, *, diagnostics: list[dict] | None = None,
    dependency_fingerprints: dict[str, str] | None = None,
    evidence_content_fingerprints: dict[str, str] | None = None,
    evidence_locator_fingerprints: dict[str, str] | None = None,
) -> list[dict]:
    by_id = {row["source_id"]: row for row in rows}
    groups: dict[tuple, list[ReviewDecision]] = defaultdict(list)
    for decision in load_decisions(directory):
        if decision.subject_type != "source":
            continue
        if decision.review_type != "identity":
            _diagnose(diagnostics, "unsupported_review_type", decision)
            continue
        row = by_id.get(decision.subject_id)
        if not row:
            _diagnose(diagnostics, "missing_subject", decision)
            continue
        if not _matches(
            decision, row, by_id, dependency_fingerprints, evidence_content_fingerprints,
            evidence_locator_fingerprints, diagnostics,
        ):
            continue
        if not _evidence_source_ids(decision) <= set(by_id):
            _diagnose(diagnostics, "missing_evidence_source", decision)
            continue
        key = (decision.subject_id, decision.review_type, decision.input_fingerprint or decision.input_sha256)
        groups[key].append(decision)

    for (subject_id, review_type, _digest), decisions in groups.items():
        row = by_id[subject_id]
        conclusions = {d.conclusion for d in decisions}
        values = {json.dumps(d.applied_values(), ensure_ascii=False, sort_keys=True) for d in decisions}
        if len(conclusions) == 1 and len(values) == 1:
            row["verification_status"] = decisions[0].conclusion
        else:
            raise ValueError(_conflict_error(subject_id, review_type, decisions))
    return rows


def apply_document_decisions(
    rows: list[dict], source_rows: list[dict], directory: Path,
    *, diagnostics: list[dict] | None = None,
    dependency_fingerprints: dict[str, str] | None = None,
    evidence_content_fingerprints: dict[str, str] | None = None,
    evidence_locator_fingerprints: dict[str, str] | None = None,
) -> list[dict]:
    """Apply reviewed metadata decisions to documents.

    Invariant: for any given (subject_id, review_type, input_sha256) group,
    there must be exactly one applicable decision (or true duplicates).
    Conflicting decisions — where distinct conclusions or values exist — raise
    ValueError so the registry build fails explicitly rather than silently
    resolving via filename sort order.
    """
    sources = {row["source_id"]: row for row in source_rows}
    by_id = {row["doc_id"]: row for row in rows}
    allowed = {"title", "issued_date", "valid_from", "aliases"}
    groups: dict[tuple, list[ReviewDecision]] = defaultdict(list)

    for decision in load_decisions(directory):
        if decision.subject_type != "document":
            continue
        if decision.review_type != "metadata":
            _diagnose(diagnostics, "unsupported_review_type", decision)
            continue
        row = by_id.get(decision.subject_id)
        if not row:
            _diagnose(diagnostics, "missing_subject", decision)
            continue
        if not _matches(
            decision, row, sources, dependency_fingerprints, evidence_content_fingerprints,
            evidence_locator_fingerprints, diagnostics,
        ):
            continue
        if not _evidence_source_ids(decision) <= set(row["source_ids"]):
            _diagnose(diagnostics, "evidence_not_in_subject", decision)
            continue
        applied_values = decision.applied_values()
        if not set(applied_values) <= allowed:
            raise ValueError(f"Document decision for {decision.subject_id!r} has unsupported fields: "
                             f"{set(applied_values) - allowed}")
        key = (decision.subject_id, decision.review_type, decision.input_fingerprint or decision.input_sha256)
        groups[key].append(decision)

    for (subject_id, review_type, _digest), decisions in groups.items():
        row = by_id[subject_id]
        value_keys = {json.dumps(d.applied_values(), ensure_ascii=False, sort_keys=True) for d in decisions}
        conclusion_keys = {d.conclusion for d in decisions}
        if len(value_keys) == 1 and len(conclusion_keys) == 1:
            # True duplicates or single decision — safe to apply
            d = decisions[0]
            row.update(d.applied_values())
            row["verification_status"] = d.conclusion
        else:
            raise ValueError(_conflict_error(subject_id, review_type, decisions))

    return rows

def apply_coverage_decisions(
    rows: list[dict], source_rows: list[dict], directory: Path,
    *, diagnostics: list[dict] | None = None,
    dependency_fingerprints: dict[str, str] | None = None,
    evidence_content_fingerprints: dict[str, str] | None = None,
    evidence_locator_fingerprints: dict[str, str] | None = None,
) -> list[dict]:
    """Apply only explicit v2 coverage decisions; metadata never implies coverage."""
    sources = {row["source_id"]: row for row in source_rows}
    by_id = {f"coverage:{row['topic']}:{row['doc_number']}": row for row in rows}
    groups: dict[tuple, list[ReviewDecision]] = defaultdict(list)
    for decision in load_decisions(directory):
        if decision.subject_type != "coverage":
            continue
        if decision.review_type != "coverage":
            _diagnose(diagnostics, "unsupported_review_type", decision)
            continue
        row = by_id.get(decision.subject_id)
        if not row:
            _diagnose(diagnostics, "missing_subject", decision)
            continue
        if not _matches(
            decision, row, sources, dependency_fingerprints, evidence_content_fingerprints,
            evidence_locator_fingerprints, diagnostics,
        ):
            continue
        key = (decision.subject_id, decision.review_type, decision.input_fingerprint)
        groups[key].append(decision)
    for (subject_id, review_type, _digest), decisions in groups.items():
        outcomes = {(decision.conclusion, canonical_hash(decision.applied_values())) for decision in decisions}
        if len(outcomes) != 1:
            raise ValueError(_conflict_error(subject_id, review_type, decisions))
        row = by_id[subject_id]
        row.update(decisions[0].applied_values())
        row["verification_status"] = decisions[0].conclusion
    return rows
