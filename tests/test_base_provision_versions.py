from backend.ingestion.chunker_v2 import chunk_articles
from backend.ingestion.parser import parse_legal_document
import copy
import hashlib

import pytest
from pydantic import ValidationError

from backend.ingestion.version_builder import base_versions, materialize_versions
from backend.ingestion.schema import Operation


def test_base_version_keeps_full_parent_and_pending_validity():
    """Schema v2: each provision (article + items) becomes a separate version.
    Input with 2 items produces 3 versions: article:1, item:1, item:2.
    All must be pending (no verified evidence yet) and have valid_from=None.
    """
    parsed = parse_legal_document(
        "\u0110i\u1ec1u 1. Ph\u1ea1m vi\n1. N\u1ed9i dung th\u1ee9 nh\u1ea5t.\n2. N\u1ed9i dung th\u1ee9 hai.",
        {"doc_id": "doc:example", "doc_number": "example", "doc_title": "Example",
         "doc_type": "luat", "valid_from": "2025-01-01"},
    )
    chunks = chunk_articles(parsed, release_id="candidate-test", source_id="src:example",
                            source_url=None, max_chars=55)
    versions = base_versions({"doc:example": parsed}, chunks)

    # Schema v2: article:1 + article:1/item:1 + article:1/item:2 = 3 provisions
    assert len(versions) == 3

    # All chunks must map to one of the versions
    version_ids = {v["provision_version_id"] for v in versions}
    assert {chunk["provision_version_id"] for chunk in chunks} == version_ids

    # All versions must be pending with no verified dates
    for v in versions:
        assert v["verification_status"] == "pending"
        assert v["valid_from"] is None
        assert v["source_refs"]

    # Provision IDs must cover the expected structural paths
    provision_ids = {v["provision_id"] for v in versions}
    assert "doc:example:body/article:1" in provision_ids
    assert "doc:example:body/article:1/item:1" in provision_ids
    assert "doc:example:body/article:1/item:2" in provision_ids


def _hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _version(doc, path, content, *, valid_from="2015-01-01", source="src:test"):
    provision = f"{doc}:{'/'.join(path)}"
    return {
        "doc_id": doc, "provision_id": provision,
        "provision_version_id": f"{provision}@{_hash(content)[:16]}",
        "structural_path": path, "content_kind": "normative", "content": content,
        "valid_from": valid_from, "valid_to": None, "verification_status": "pending",
        "source_refs": [{"source_id": source, "locator": "page:1", "source_url": None}],
        "applied_relation_ids": [],
    }


def _replace_fixture():
    target = _version("doc:1", ["body", "article:1", "item:1"], "Original", source="src:target")
    instruction = _version(
        "doc:2", ["body", "article:1", "item:1"], "Replace item 1 as follows:",
        valid_from="2024-01-01", source="src:amendment",
    )
    payload = _version(
        "doc:2", ["body", "article:1", "item:1", "amendment_payload", "item:1"],
        "Amended text", valid_from="2024-01-01", source="src:amendment",
    )
    operation = {
        "operation_id": "op-replace-1", "relation_id": "rel:1",
        "source_clause": instruction["provision_id"], "source_hash": _hash(instruction["content"]),
        "target_locator": target["provision_id"], "target_hash": _hash(target["content"]),
        "verb": "replace", "effective_from": "2025-01-01", "review_status": "verified",
        "population_predicate": "general",
        "payload_refs": [payload["provision_id"]], "payload_hash": _hash(payload["content"]),
    }
    return [target, instruction, payload], operation


def test_materialization_validates_hashes_preserves_inputs_and_payload_provenance():
    versions, operation = _replace_fixture()
    sibling = _version("doc:1", ["body", "article:1", "item:2"], "Untouched", source="src:target")
    versions.append(sibling)
    before = copy.deepcopy(versions)
    materialized = materialize_versions(versions, [operation])
    assert versions == before
    original = next(row for row in materialized if row["content"] == "Original")
    amended = next(row for row in materialized if row["content"] == "Amended text"
                   and row["doc_id"] == "doc:1")
    assert original["valid_to"] == "2025-01-01"
    assert amended["valid_from"] == "2025-01-01"
    assert amended["source_refs"][0]["source_id"] == "src:amendment"
    assert amended["provision_version_id"] != operation["target_locator"] + "@" + _hash("Amended text")[:16]
    untouched = next(row for row in materialized if row["content"] == "Untouched")
    assert untouched["valid_to"] is None


@pytest.mark.parametrize("field,value", [
    ("source_hash", "unknown"), ("target_hash", None), ("target_hash", "0" * 64),
])
def test_materialization_rejects_missing_unknown_or_false_hashes(field, value):
    versions, operation = _replace_fixture()
    operation[field] = value
    with pytest.raises(ValueError, match="hash|Stale"):
        materialize_versions(versions, [operation])


def test_materialization_rejects_inline_payload_mismatch_and_stale_ref():
    versions, operation = _replace_fixture()
    operation["payload"] = "not the referenced payload"
    with pytest.raises(ValueError, match="Inline payload differs"):
        materialize_versions(versions, [operation])
    operation.pop("payload")
    operation["payload_refs"] = ["doc:2:body/article:1/item:1/amendment_payload/item:missing"]
    with pytest.raises(ValueError, match="payload ref"):
        materialize_versions(versions, [operation])


def test_materialization_rejects_unknown_population():
    versions, operation = _replace_fixture()
    operation["population_predicate"] = None
    with pytest.raises(ValueError, match="Unknown population"):
        materialize_versions(versions, [operation])


def test_verified_operation_schema_rejects_placeholder_hashes():
    _, operation = _replace_fixture()
    operation["source_hash"] = "unknown"
    with pytest.raises(ValidationError, match="real SHA-256"):
        Operation.model_validate(operation)


def test_materialization_rejects_broad_replace_and_allows_add_with_parent():
    versions, operation = _replace_fixture()
    operation["target_locator"] = "doc:1:body"
    with pytest.raises(ValueError, match="Broad content target"):
        materialize_versions(versions, [operation])

    parent = _version("doc:1", ["body", "article:2"], "Article 2", source="src:target")
    instruction = versions[1]
    payload = versions[2]
    add = {
        **operation,
        "operation_id": "op-add-1", "verb": "add",
        "target_locator": "doc:1:body/article:2/item:1", "target_hash": _hash(""),
        "source_hash": _hash(instruction["content"]),
    }
    result = materialize_versions([parent, instruction, payload], [add])
    added = next(row for row in result if row["provision_id"] == add["target_locator"])
    assert added["content"] == "Amended text"


def test_scoped_amendment_requires_unique_precondition():
    versions, operation = _replace_fixture()
    operation.update({
        "verb": "scoped_amendment", "match_text": "Original",
        "payload_hash": _hash("Amended text"),
    })
    result = materialize_versions(versions, [operation])
    assert any(row["doc_id"] == "doc:1" and row["content"] == "Amended text" for row in result)
    operation["match_text"] = "missing"
    with pytest.raises(ValueError, match="precondition failed"):
        materialize_versions(versions, [operation])


def test_repeated_edits_keep_distinct_timeline_instances_when_content_reappears():
    versions, first = _replace_fixture()
    instruction = _version(
        "doc:2", ["body", "article:1", "item:2"], "Replace again:",
        valid_from="2024-01-01", source="src:amendment",
    )
    payload = _version(
        "doc:2", ["body", "article:1", "item:2", "amendment_payload", "item:1"],
        "Original", valid_from="2024-01-01", source="src:amendment",
    )
    second = {
        **first, "operation_id": "op-replace-2", "relation_id": "rel:2",
        "source_clause": instruction["provision_id"], "source_hash": _hash(instruction["content"]),
        "target_hash": _hash("Amended text"), "effective_from": "2026-01-01",
        "payload_refs": [payload["provision_id"]], "payload_hash": _hash(payload["content"]),
        "transition_rule": "new applications only",
    }
    result = materialize_versions(versions + [instruction, payload], [second, first])
    target = [row for row in result if row["doc_id"] == "doc:1"]
    assert [(row["content"], row["valid_from"], row["valid_to"]) for row in target] == [
        ("Original", "2015-01-01", "2025-01-01"),
        ("Amended text", "2025-01-01", "2026-01-01"),
        ("Original", "2026-01-01", None),
    ]
    assert len({row["provision_version_id"] for row in target}) == 3
    assert target[-1]["transition_rule"] == "new applications only"
