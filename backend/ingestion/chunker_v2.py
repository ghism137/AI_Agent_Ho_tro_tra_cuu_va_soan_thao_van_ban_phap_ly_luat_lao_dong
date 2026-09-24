"""Deterministic search chunks from parsed legal articles."""

from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any

from backend.ingestion.schema import Chunk, SourceRef


NAMESPACE = uuid.UUID("81d3124d-2458-46e6-b027-e2f411ee99ba")
CLAUSE = re.compile(r"^(\d+)\.\s")
POINT = re.compile(r"^([a-zđ])\)\s", re.I)


def _parts(article: dict[str, Any], max_chars: int) -> list[tuple[str, list[str], bool, list[str]]]:
    lines = article["content"].splitlines()
    segments = article.get("content_segments")
    if segments:
        line_locators = [segment["locator"] for segment in segments for _ in segment["text"].splitlines()]
        if len(line_locators) != len(lines):
            raise ValueError("Source segments do not align with article content")
    else:
        # Older parsed fixtures may only carry whole-article provenance.
        if "source_locators" in article and article["source_locators"]:
            if len(article["source_locators"]) == len(lines):
                line_locators = article["source_locators"]
            else:
                line_locators = [article["source_locators"][0]] * len(lines)
        else:
            line_locators = [""] * len(lines)
    if len(article["content"]) <= max_chars:
        return [(article["content"], sorted({m[1] for line in lines if (m := CLAUSE.match(line))}),
                 False, list(dict.fromkeys(line_locators)))]
    title = lines[0]
    groups: list[tuple[str, list[str], bool, list[str]]] = []
    current = [title]
    current_locators = [line_locators[0]]
    clauses: list[str] = []
    for line, locator in zip(lines[1:], line_locators[1:], strict=True):
        clause = CLAUSE.match(line)
        if len("\n".join(current + [line])) > max_chars and len(current) > 1:
            groups.append(("\n".join(current), clauses.copy(), bool(clauses and not clause),
                           list(dict.fromkeys(current_locators))))
            current = [title]
            current_locators = [line_locators[0]]
            clauses = []
        if len(line) > max_chars:
            # Split only at sentence boundaries; retain the full parent article.
            sentences = re.split(r"(?<=[.;])\s+", line)
            for sentence in sentences:
                if len("\n".join(current + [sentence])) > max_chars and len(current) > 1:
                    groups.append(("\n".join(current), clauses.copy(), True,
                                   list(dict.fromkeys(current_locators))))
                    current = [title]
                    current_locators = [line_locators[0]]
                    clauses = []
                current.append(sentence)
                current_locators.append(locator)
        else:
            current.append(line)
            current_locators.append(locator)
        if clause:
            clauses.append(clause[1])
    if len(current) > 1:
        groups.append(("\n".join(current), clauses, len(groups) > 0 and not clauses,
                       list(dict.fromkeys(current_locators))))
    return groups


def chunk_articles(
    parsed: dict[str, Any],
    *,
    release_id: str,
    source_id: str,
    source_url: str | None,
    max_chars: int = 4000,
) -> list[dict[str, Any]]:
    meta = parsed["metadata"]
    output = []
    for article in parsed["articles"]:
        path = article["structural_path"]
        provision_id = f"{meta['doc_id']}:{'/'.join(path)}"
        full_hash = hashlib.sha256(article["content"].encode("utf-8")).hexdigest()
        version_id = f"{provision_id}@{full_hash[:16]}"
        for index, (content, clause_numbers, fragment, locators) in enumerate(_parts(article, max_chars), 1):
            source_refs = [SourceRef(source_id=source_id, source_url=source_url, locator=locator)
                           for locator in locators]
            if len(content) > max_chars:
                raise ValueError(f"Chunk exceeds character safety budget: {provision_id} part {index}")
            digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
            chunk_id = str(uuid.uuid5(NAMESPACE, f"{version_id}:{index}:{digest}"))
            record = Chunk.model_validate({
                "release_id": release_id, "chunk_id": chunk_id, "provision_id": provision_id,
                "provision_version_id": version_id, "doc_id": meta["doc_id"],
                "doc_number": meta["doc_number"], "doc_title": meta["doc_title"],
                "doc_type": meta["doc_type"], "content_kind": article["content_kind"],
                "structural_path": path, "article_number": article["article_number"] if article["article_number"] != "ALL" else None,
                "clause_numbers": clause_numbers, "point_letters": [], "parent_id": version_id,
                "hierarchy_path": article["hierarchy_path"], "issued_date": meta.get("issued_date"),
                "valid_from": meta.get("valid_from") if meta.get("verification_status") == "verified" else None,
                "valid_to": None,
                "proposed_valid_from": meta.get("valid_from"),
                "proposed_valid_to": None,
                "verification_status": "pending", "content": content, "content_hash": digest,
                "content_length": len(content), "token_count": None, "is_fragment": fragment,
                "topic_tags": meta.get("topic_tags", []), "source_refs": source_refs,
                "applied_relation_ids": [],
            }).model_dump(mode="json")
            output.append(record)
    seen = set()
    dedup = []
    for row in output:
        if row["chunk_id"] not in seen:
            seen.add(row["chunk_id"])
            dedup.append(row)
    return dedup

def chunk_versions(
    versions: list[dict[str, Any]],
    parsed: dict[str, Any],
    release_id: str,
    max_chars: int = 4000
) -> list[dict[str, Any]]:
    # Index articles to recover hierarchy_path and source refs
    article_index = {}
    for doc_parsed in parsed.values():
        doc_id = doc_parsed["metadata"]["doc_id"]
        for art in doc_parsed["articles"]:
            prov_id = f"{doc_id}:{'/'.join(art['structural_path'])}"
            article_index[prov_id] = art
            
    final_chunks = []
    for v in versions:
        doc_id_raw = v["doc_id"]
        doc_parsed = parsed.get(doc_id_raw)
        if not doc_parsed:
            continue
            
        meta = doc_parsed["metadata"]
        prov_id = v["provision_id"]
        orig_art = article_index.get(prov_id)
            
        loc_to_refs = {}
        for ref in v.get("source_refs", []):
            loc = ref["locator"]
            if loc not in loc_to_refs:
                loc_to_refs[loc] = []
            loc_to_refs[loc].append(ref)
            
        locators_flat = list(loc_to_refs.keys())
            
        mock_article = {
            "content": v["content"],
            "source_locators": locators_flat
        }
        version_id = v["provision_version_id"]
        
        art_num = orig_art["article_number"] if orig_art and orig_art["article_number"] != "ALL" else None
        hierarchy = orig_art["hierarchy_path"] if orig_art else ""
        
        for index, (content, clause_numbers, fragment, locators) in enumerate(_parts(mock_article, max_chars), 1):
            source_refs_dicts = []
            for loc in locators:
                source_refs_dicts.extend(loc_to_refs.get(loc, []))
            
            source_refs = [SourceRef(**ref) for ref in source_refs_dicts]
            if not source_refs and locators:
                # Data-contract violation: every version reaching chunk_versions must
                # carry source_refs that cover its locators. Materialised versions
                # inherit source_refs from their base version (version_builder.py,
                # `new_v = dict(v)`). Base versions must have source_refs populated
                # by chunk_articles (which always assigns a real source_id from the
                # registry). Reaching this branch means a version arrived here without
                # provenance — fabricating a source_id from structural_path (e.g.
                # "article:1") is never acceptable; fail loudly instead.
                raise ValueError(
                    f"Data-contract violation: version {version_id} has locators "
                    f"{locators!r} but no matching source_refs. "
                    "All versions must carry valid source_refs before chunk_versions."
                )
            if len(content) > max_chars:
                raise ValueError(f"Chunk exceeds character safety budget: {prov_id} part {index}")
            digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
            chunk_id = str(uuid.uuid5(NAMESPACE, f"{version_id}:{index}:{digest}"))
            
            record = Chunk.model_validate({
                "release_id": release_id, "chunk_id": chunk_id, "provision_id": prov_id,
                "provision_version_id": version_id, "doc_id": v["doc_id"],
                "doc_number": meta["doc_number"], "doc_title": meta["doc_title"],
                "doc_type": meta["doc_type"], "content_kind": v["content_kind"],
                "structural_path": v["structural_path"], "article_number": art_num,
                "clause_numbers": clause_numbers, "point_letters": [], "parent_id": version_id,
                "hierarchy_path": hierarchy, "issued_date": meta.get("issued_date"),
                "valid_from": v.get("valid_from"),
                "valid_to": v.get("valid_to"),
                "proposed_valid_from": v.get("proposed_valid_from"),
                "proposed_valid_to": v.get("proposed_valid_to"),
                "population_predicate": v.get("population_predicate"),
                "transition_rule": v.get("transition_rule"),
                "verification_status": v.get("verification_status", "pending"), "content": content, "content_hash": digest,
                "content_length": len(content), "token_count": None, "is_fragment": fragment,
                "topic_tags": meta.get("topic_tags", []), "source_refs": source_refs,
                "applied_relation_ids": v.get("applied_relation_ids", [])
            }).model_dump(mode="json")
            final_chunks.append(record)
            
    return final_chunks

