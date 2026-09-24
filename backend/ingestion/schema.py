"""Phase 1 source, provision and release contracts."""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


Status = Literal["pending", "verified", "rejected"]
Kind = Literal["normative", "annex", "form", "commentary"]
ReviewType = Literal["identity", "metadata", "fidelity", "effect", "operation", "coverage"]
ReviewSubjectType = Literal["source", "document", "relation", "operation", "coverage"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceRef(StrictModel):
    source_id: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    full_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    locator: str = Field(min_length=1, pattern=r".*\S.*")
    locator_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_url: HttpUrl | None = None


class ReviewDependency(StrictModel):
    dependency_id: str = Field(min_length=1, pattern=r".*\S.*")
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")


class ReviewBindingIndex(StrictModel):
    schema_version: Literal[1] = 1
    source_full_content_sha256: dict[str, str] = Field(default_factory=dict)
    locator_sha256: dict[str, str] = Field(default_factory=dict)
    dependency_fingerprints: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_hashes(self) -> "ReviewBindingIndex":
        for group_name, values in (
            ("source_full_content_sha256", self.source_full_content_sha256),
            ("locator_sha256", self.locator_sha256),
            ("dependency_fingerprints", self.dependency_fingerprints),
        ):
            invalid = [key for key, value in values.items() if not re.fullmatch(r"[0-9a-f]{64}", value)]
            if invalid:
                raise ValueError(f"{group_name} contains invalid SHA-256 values for: {sorted(invalid)}")
        return self


class ReviewDecision(StrictModel):
    """Immutable reviewer decision.

    Version 1 is retained only so historical decisions remain replayable. New
    decisions use version 2 and bind the complete subject, evidence locators,
    source bytes and every upstream review dependency.
    """

    decision_version: Literal[1, 2] = 1
    subject_type: ReviewSubjectType
    subject_id: str
    review_type: ReviewType
    input_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    input_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    conclusion: Literal["verified", "rejected"]
    evidence_source_id: str | None = None
    evidence_locator: str | None = None
    evidence_url: HttpUrl | None = None
    evidence: list[EvidenceRef] = Field(default_factory=list)
    dependencies: list[ReviewDependency] = Field(default_factory=list)
    reviewer: str
    reviewed_at: date
    proposed_values: dict[str, Any] = Field(default_factory=dict)
    verified_values: dict[str, Any] = Field(default_factory=dict)
    values: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_decision(self) -> "ReviewDecision":
        if not self.reviewer.strip():
            raise ValueError("review requires an actual reviewer")
        if self.decision_version == 1:
            if not self.input_sha256 or not self.evidence_source_id or not self.evidence_locator:
                raise ValueError("legacy review requires input hash and evidence locator")
            applied = self.values
        else:
            if not self.input_fingerprint or not self.evidence:
                raise ValueError("v2 review requires input fingerprint and typed evidence")
            if self.input_sha256 or self.evidence_source_id or self.evidence_locator or self.values:
                raise ValueError("v2 review cannot mix legacy hash, evidence or values fields")
            applied = self.verified_values
            dependency_ids = [item.dependency_id for item in self.dependencies]
            if len(dependency_ids) != len(set(dependency_ids)):
                raise ValueError("review dependencies must be unique")
            if self.conclusion == "verified" and not self.dependencies:
                raise ValueError("verified v2 review requires typed dependencies")
        if self.conclusion == "verified" and self.review_type == "metadata":
            if not all(applied.get(key) for key in ("title", "issued_date", "valid_from")):
                raise ValueError("verified metadata requires title, issued_date and valid_from")
        if self.conclusion == "verified" and self.review_type in {"effect", "operation", "coverage"}:
            if self.decision_version != 2:
                raise ValueError(f"verified {self.review_type} review requires version 2")
        return self

    def applied_values(self) -> dict[str, Any]:
        if self.conclusion != "verified":
            return {}
        return self.values if self.decision_version == 1 else self.verified_values


class AcceptanceEnvelope(StrictModel):
    schema_version: Literal[1] = 1
    candidate_id: str
    content_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    evidence_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    scope_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewer: str
    reviewed_at: date

    @model_validator(mode="after")
    def reviewer_required(self) -> "AcceptanceEnvelope":
        if not self.reviewer.strip():
            raise ValueError("acceptance envelope requires an actual reviewer")
        return self


class Source(StrictModel):
    source_id: str
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    format: Literal["md", "docx", "html", "pdf"]
    source_url: HttpUrl | None = None
    collected_at: date | None = None
    verification_status: Status = "pending"
    extraction_method: str | None = None
    source_role: Literal["body", "annex", "form", "continuation", "alternate", "body_and_forms"] | None = None


class Document(StrictModel):
    doc_id: str
    doc_number: str
    title: str
    doc_type: str
    issued_date: date | None = None
    valid_from: date | None = None
    source_refs: list[SourceRef]
    is_quarantined: bool = False

class Operation(StrictModel):
    operation_id: str
    relation_id: str | None = None
    source_clause: str
    source_hash: str | None = None
    target_locator: str | None = None
    target_hash: str | None = None
    verb: Literal["replace", "add", "delete", "renumber", "repeal", "scoped_amendment", "applicability"]
    payload: str | None = None
    payload_source: str | None = None
    payload_refs: list[str] = Field(default_factory=list)
    payload_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    match_text: str | None = None
    ordering: int | None = None
    preconditions: list[str] = Field(default_factory=list)
    effective_from: date | None = None
    effective_to: date | None = None
    population_predicate: str | None = None
    transition_rule: str | None = None
    review_refs: list[str] = Field(default_factory=list)
    review_status: Status = "pending"

    @model_validator(mode="after")
    def validate_operation(self) -> "Operation":
        if self.verb != "applicability" and not self.relation_id:
            raise ValueError("operation requires relation_id unless verb is applicability")
        if self.verb == "applicability":
            if not (self.source_clause and self.source_hash and self.effective_from and self.review_status == "verified"):
                raise ValueError("applicability event missing mandatory fields")
            if self.target_locator and not self.target_hash:
                raise ValueError("applicability event with target requires target_hash")
        if self.review_status == "verified":
            if not all([self.source_hash, self.target_hash, self.effective_from, self.population_predicate]):
                raise ValueError("verified operation requires hashes, date and population")
            if not all(re.fullmatch(r"[0-9a-f]{64}", value or "")
                       for value in (self.source_hash, self.target_hash)):
                raise ValueError("verified operation requires real SHA-256 hashes")
            if self.verb in {"replace", "add", "scoped_amendment"}:
                if not self.payload_refs or not self.payload_hash:
                    raise ValueError("verified content operation requires payload refs and hash")
                if any("amendment_payload" not in ref for ref in self.payload_refs):
                    raise ValueError("payload refs must address amendment_payload paths")
            if self.verb == "scoped_amendment" and not self.match_text:
                raise ValueError("verified scoped amendment requires match_text")
        return self

class ParsedDocument(StrictModel):
    doc_id: str
    doc_number: str
    title: str
    doc_type: str
    issued_date: date | None = None
    valid_from: date | None = None
    source_ids: list[str]
    aliases: list[str] = Field(default_factory=list)
    verification_status: Status = "pending"


class SourceRef(StrictModel):
    source_id: str
    locator: str
    source_url: HttpUrl | None = None


class ProvisionVersion(StrictModel):
    schema_version: Literal[2] = 2
    provision_id: str
    provision_version_id: str
    doc_id: str
    structural_path: list[str]
    content_kind: Kind
    content: str
    valid_from: date | None = None
    valid_to: date | None = None
    proposed_valid_from: date | None = None
    proposed_valid_to: date | None = None
    population_predicate: str | None = None
    transition_rule: str | None = None
    verification_status: Status = "pending"
    source_refs: list[SourceRef]
    applied_relation_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_interval(self) -> "ProvisionVersion":
        if self.valid_from and self.valid_to and self.valid_to <= self.valid_from:
            raise ValueError("valid_to must be later than valid_from")
        if self.verification_status == "verified" and self.content_kind == "normative":
            if not self.valid_from or not self.source_refs:
                raise ValueError("verified normative provision requires valid_from and source_refs")
        return self


class Chunk(StrictModel):
    schema_version: Literal[2] = 2
    release_id: str
    chunk_id: str
    provision_id: str
    provision_version_id: str
    doc_id: str
    doc_number: str
    doc_title: str
    doc_type: str
    content_kind: Kind
    structural_path: list[str]
    article_number: str | None = None
    clause_numbers: list[str] = Field(default_factory=list)
    point_letters: list[str] = Field(default_factory=list)
    parent_id: str | None = None
    hierarchy_path: str = ""
    issued_date: date | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    proposed_valid_from: date | None = None
    proposed_valid_to: date | None = None
    population_predicate: str | None = None
    transition_rule: str | None = None
    verification_status: Status
    content: str
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_length: int = Field(ge=0)
    token_count: int | None = Field(default=None, ge=0)
    is_fragment: bool = False
    topic_tags: list[str] = Field(default_factory=list)
    source_refs: list[SourceRef]
    applied_relation_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_chunk(self) -> "Chunk":
        if len(self.content) != self.content_length:
            raise ValueError("content_length mismatch")
        if self.valid_from and self.valid_to and self.valid_to <= self.valid_from:
            raise ValueError("invalid validity interval")
        if self.verification_status == "verified" and self.content_kind == "normative":
            if not self.valid_from or not self.source_refs:
                raise ValueError("verified normative chunk requires validity and source")
        return self


class Relation(StrictModel):
    relation_id: str
    relation_type: Literal["references", "guides", "amends", "supplements", "replaces", "repeals"]
    source_doc_id: str
    source_provision_id: str | None = None
    target_doc_id: str
    target_locators: list[list[str]]
    scope: Literal["document", "provision", "fragment", "unknown"]
    operation: str
    effective_from: date | None = None
    effective_to: date | None = None
    evidence_source_id: str | None = None
    evidence_locator: str | None = None
    review_status: Status = "pending"
    reviewed_by: str | None = None
    reviewed_at: date | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def verified_requires_evidence(self) -> "Relation":
        if self.review_status == "verified":
            if not all([self.effective_from, self.evidence_source_id, self.evidence_locator, self.reviewed_by, self.reviewed_at]):
                raise ValueError("verified relation requires date, evidence and reviewer")
            if self.scope == "unknown":
                raise ValueError("verified relation requires resolved scope")
        return self
