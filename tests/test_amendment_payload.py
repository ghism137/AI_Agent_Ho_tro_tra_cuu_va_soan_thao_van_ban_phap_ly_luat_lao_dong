"""Tests for amendment_payload state machine in parser.flush()."""
import pytest
from backend.ingestion.parser import parse_legal_document


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def paths_for(articles, *, starts_with=None, exact=None):
    """Return structural_path lists from result, optionally filtered."""
    result = [a["structural_path"] for a in articles]
    if starts_with:
        result = [p for p in result if "/".join(p).startswith(starts_with)]
    if exact:
        result = [p for p in result if "/".join(p) == exact]
    return result


def all_paths(result):
    return ["/".join(a["structural_path"]) for a in result["articles"]]


# ---------------------------------------------------------------------------
# Regression guard: non-amendment articles unaffected
# ---------------------------------------------------------------------------

def test_non_amendment_article_paths_unchanged():
    text = (
        "Điều 1. Phạm vi\n"
        "1. Người lao động.\n"
        "2. Người sử dụng lao động.\n"
        "Điều 2. Điều khoản thi hành\n"
        "a) Điều kiện a.\n"
        "b) Điều kiện b."
    )
    result = parse_legal_document(text, {"doc_number": "45/2019/QH14"})
    ps = all_paths(result)
    assert "body/article:1" in ps
    assert "body/article:1/item:1" in ps
    assert "body/article:1/item:2" in ps
    assert "body/article:2" in ps
    assert "body/article:2/item:1/point:a" not in ps  # no outer item → point is direct
    # Ensure no amendment_payload appears
    assert not any("amendment_payload" in p for p in ps)


# ---------------------------------------------------------------------------
# Core case A: outer amendment item → quoted article replacement
# ---------------------------------------------------------------------------

def test_amendment_payload_single_article_replacement():
    """
    Điều 1 item:1 instructs Sửa đổi + "như sau:", then quoted Điều 14.
    Payload lines must be at body/article:1/item:1/amendment_payload/article:14.
    item:1 of the outer amendment must NOT collide with quoted text.
    """
    text = (
        "Điều 1. Sửa đổi, bổ sung một số điều của Nghị định 146/2018/NĐ-CP\n"
        '1. Sửa đổi Điều 14 như sau:\n'
        '"Điều 14. Mức hưởng bảo hiểm y tế\n'
        "1. Người lao động đóng BHYT.\n"
        "2. Người phụ thuộc.\n"
        '"'  # closing quote
    )
    result = parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})
    ps = all_paths(result)
    # Outer item must exist at body/article:1/item:1
    assert "body/article:1/item:1" in ps
    # Payload article at correct path
    assert "body/article:1/item:1/amendment_payload/article:14" in ps
    # Payload khoản at correct path
    assert "body/article:1/item:1/amendment_payload/article:14/item:1" in ps
    assert "body/article:1/item:1/amendment_payload/article:14/item:2" in ps
    # item:1 at body/article:1 level must NOT contain the quoted khoản content
    outer_item = next(a for a in result["articles"] if "/".join(a["structural_path"]) == "body/article:1/item:1")
    assert "Người lao động đóng BHYT" not in outer_item["content"]


def test_amendment_payload_two_outer_items_sequential():
    """
    Two sequential outer amendment items (1. and 2.) each with payload.
    Second outer item correctly closes payload of first.
    """
    text = (
        "Điều 1. Sửa đổi, bổ sung một số điều\n"
        '1. Sửa đổi Điều 14 như sau:\n'
        '"Điều 14. Mức hưởng BHYT\n'
        "1. Nội dung khoản 1.\n"
        '"'
        "\n"
        '2. Bổ sung Điều 15 như sau:\n'
        '"Điều 15. Mức đóng BHYT\n'
        "1. Nội dung mới.\n"
        '"'
    )
    result = parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})
    ps = all_paths(result)
    assert "body/article:1/item:1/amendment_payload/article:14" in ps
    assert "body/article:1/item:2/amendment_payload/article:15" in ps
    # No cross-contamination: item:14 content should not appear under item:2 payload
    p14 = next(a for a in result["articles"] if "/".join(a["structural_path"]) == "body/article:1/item:1/amendment_payload/article:14")
    assert "Nội dung mới" not in p14["content"]


def test_amendment_payload_clause_only_replacement():
    """
    Payload is a single clause (khoản), not a full article.
    Should produce body/.../item:N/amendment_payload/item:M.
    """
    text = (
        "Điều 1. Sửa đổi một số điều\n"
        '1. Sửa đổi khoản 3 Điều 14 như sau:\n'
        '"3. Điều kiện hưởng.\n'
        '"'
    )
    result = parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})
    ps = all_paths(result)
    assert "body/article:1/item:1/amendment_payload/item:3" in ps
    assert not any("amendment_payload/article:" in p for p in ps)


def test_amendment_payload_no_closing_quote_raises():
    """
    If payload has no closing quote and the article ends, parser must raise ValueError.
    """
    text = (
        "Điều 1. Sửa đổi một số điều\n"
        '1. Sửa đổi Điều 14 như sau:\n'
        '"Điều 14. Mức hưởng BHYT\n'
        "1. Nội dung khoản 1.\n"
        # No closing quote — article ends
    )
    with pytest.raises(ValueError, match="quarantined"):
        parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})


def test_closing_quote_on_last_clause_keeps_clause_boundary():
    text = (
        "Điều 1. Sửa đổi\n"
        "1. Sửa đổi Điều 14 như sau:\n"
        "“Điều 14. Tên\n"
        "1. Nội dung một.\n"
        "2. Nội dung hai.”"
    )
    result = parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})
    pieces = {"/".join(a["structural_path"]): a["content"] for a in result["articles"]}
    assert pieces["body/article:1/item:1/amendment_payload/article:14/item:1"] == "1. Nội dung một."
    assert pieces["body/article:1/item:1/amendment_payload/article:14/item:2"] == "2. Nội dung hai.”"


def test_quote_before_semicolon_closes_payload():
    text = (
        "Điều 1. Sửa đổi\n"
        "1. Sửa đổi Điều 14 như sau:\n"
        "“Điều 14. Tên\n"
        "1. Nội dung.”;"
    )
    result = parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})
    assert "body/article:1/item:1/amendment_payload/article:14/item:1" in all_paths(result)


def test_single_line_quoted_clause_closes_payload():
    text = (
        "Điều 1. Sửa đổi\n"
        "1. Sửa đổi khoản 3 như sau:\n"
        "“3. Nội dung.”"
    )
    result = parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})
    assert "body/article:1/item:1/amendment_payload/item:3" in all_paths(result)


def test_point_instruction_preserves_full_instruction_path():
    text = (
        "Điều 1. Sửa đổi\n"
        "1. Sửa đổi Điều 14:\n"
        "a) Sửa đổi khoản 3 như sau:\n"
        "“3. Nội dung.”"
    )
    result = parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})
    assert "body/article:1/item:1/point:a/amendment_payload/item:3" in all_paths(result)


def test_inner_amendment_verb_does_not_exit_open_quoted_payload():
    text = (
        "Điều 1. Sửa đổi\n"
        "1. Sửa đổi Điều 14 như sau:\n"
        "“Điều 14. Tên\n"
        "1. Nội dung một.\n"
        "2. Sửa đổi kỹ thuật.\n"
        "Phần còn lại.”"
    )
    result = parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})
    pieces = {"/".join(a["structural_path"]): a["content"] for a in result["articles"]}
    path = "body/article:1/item:1/amendment_payload/article:14/item:2"
    assert pieces[path] == "2. Sửa đổi kỹ thuật.\nPhần còn lại.”"
    assert "body/article:1/item:2" not in pieces


def test_unquoted_article_payload_is_not_intercepted_as_top_level_article():
    text = (
        "Điều 1. Sửa đổi\n"
        "1. Sửa đổi Điều 2 như sau:\n"
        "Điều 2. Nội dung thay thế\n"
        "1. Quy định mới."
    )
    result = parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})
    paths = all_paths(result)
    assert "body/article:1/item:1/amendment_payload/article:2" in paths
    assert "body/article:2" not in paths


def test_ordinary_intro_after_prior_amendment_clause_keeps_next_top_level_article():
    text = (
        "Điều 1. Quy định chung\n"
        "1. Sửa đổi thuật ngữ tại văn bản khác.\n"
        "2. Các trường hợp áp dụng được quy định như sau:\n"
        "Điều 2. Điều khoản thi hành\n"
        "1. Văn bản này có hiệu lực."
    )
    result = parse_legal_document(text, {"doc_number": "test"})
    paths = all_paths(result)
    assert "body/article:2" in paths
    assert not any("amendment_payload" in path for path in paths)
    article_two = next(
        article
        for article in result["articles"]
        if "/".join(article["structural_path"]) == "body/article:2"
    )
    assert article_two["content"].startswith("Điều 2. Điều khoản thi hành")


def test_wrapped_amendment_instruction_still_captures_article_payload():
    text = (
        "Điều 1. Sửa đổi một số điều\n"
        "1. Sửa đổi Điều 14 của Nghị định\n"
        "được quy định lại như sau:\n"
        "Điều 14. Nội dung thay thế\n"
        "1. Quy định mới."
    )
    result = parse_legal_document(text, {"doc_number": "test"})
    paths = all_paths(result)
    assert "body/article:1/item:1/amendment_payload/article:14" in paths
    assert "body/article:14" not in paths


@pytest.mark.parametrize(
    "closed_point",
    ["a) Sửa đổi kỹ thuật.”\n", "a) Sửa đổi kỹ thuật.\n”\n"],
)
def test_closed_quoted_payload_point_cannot_trigger_later_ordinary_intro(closed_point):
    text = (
        "Điều 1. Sửa đổi một số điều\n"
        "1. Sửa đổi Điều 14 như sau:\n"
        "“Điều 14. Nội dung thay thế\n"
        f"{closed_point}"
        "Các trường hợp thông thường được quy định như sau:\n"
        "Điều 2. Điều khoản thi hành\n"
        "1. Văn bản này có hiệu lực."
    )
    result = parse_legal_document(text, {"doc_number": "test"})
    paths = all_paths(result)
    assert "body/article:2" in paths
    article_two = next(
        article
        for article in result["articles"]
        if "/".join(article["structural_path"]) == "body/article:2"
    )
    assert article_two["content"].startswith("Điều 2. Điều khoản thi hành")


def test_unquoted_payload_quarantines_ambiguous_sequential_amendment_clause():
    text = (
        "Điều 1. Sửa đổi\n"
        "1. Sửa đổi Điều 14 như sau:\n"
        "Điều 14. Nội dung thay thế\n"
        "1. Quy định thứ nhất.\n"
        "2. Sửa đổi kỹ thuật trong nội dung thay thế."
    )
    with pytest.raises(ValueError, match="ambiguous sequential clause"):
        parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})


def test_unknown_plain_payload_is_quarantined_instead_of_duplicating_path():
    text = (
        "Điều 1. Sửa đổi\n"
        "1. Sửa đổi nội dung như sau:\n"
        "“Nội dung thay thế.”"
    )
    with pytest.raises(ValueError, match="unsupported start"):
        parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})


def test_instruction_without_payload_is_quarantined():
    text = "Điều 1. Sửa đổi\n1. Sửa đổi Điều 14 như sau:"
    with pytest.raises(ValueError, match="ended without a payload"):
        parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})


def test_unquoted_nested_points_close_at_article_boundary():
    text = (
        "Điều 1. Sửa đổi\n"
        "8. Sửa đổi mẫu như sau:\n"
        "a) Thay cụm từ thứ nhất;\n"
        "b) Thay cụm từ thứ hai.\n"
        "Điều 2. Bãi bỏ mẫu cũ"
    )
    result = parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})
    paths = all_paths(result)
    assert "body/article:1/item:8/amendment_payload/point:a" in paths
    assert "body/article:1/item:8/amendment_payload/point:b" in paths
    assert "body/article:2" in paths


def test_amendment_without_nhu_sau_is_not_payload():
    """
    An item that says 'Sửa đổi ...' but does NOT end with 'như sau:' should NOT
    trigger payload mode. Items that follow are outer items, not payload content.
    """
    text = (
        "Điều 1. Sửa đổi một số điều\n"
        "1. Sửa đổi từ ngữ trong Điều 14.\n"
        "2. Bổ sung quy định mới.\n"
        "Điều 2. Điều khoản thi hành"
    )
    result = parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})
    ps = all_paths(result)
    # No amendment_payload at all
    assert not any("amendment_payload" in p for p in ps)
    # Both outer items present
    assert "body/article:1/item:1" in ps
    assert "body/article:1/item:2" in ps


def test_next_top_level_dieu_exits_payload_without_close_quote():
    """
    If a new top-level Điều appears and parser detects it via article_number
    sequential ordering, payload from previous Điều must already be closed.
    Specifically: a valid, source-delimited article close exits the payload.
    (This tests Exit C path via the flush() call at end of article loop.)
    """
    # Two separate điều — first has open payload, second has Điều 2 instruction
    text = (
        "Điều 1. Sửa đổi một số điều\n"
        '1. Sửa đổi Điều 14 như sau:\n'
        '"Điều 14. Nội dung mới\n'
        "Toàn bộ nội dung.\n"
        '"'  # closes payload
        "\n"
        "Điều 2. Điều khoản thi hành\n"
        "Luật này có hiệu lực."
    )
    result = parse_legal_document(text, {"doc_number": "02/2025/NĐ-CP"})
    ps = all_paths(result)
    assert "body/article:2" in ps
    # No contamination of Điều 2
    a2 = next(a for a in result["articles"] if "/".join(a["structural_path"]) == "body/article:2")
    assert "Nội dung mới" not in a2["content"]


# ---------------------------------------------------------------------------
# Review decisions conflict detection
# ---------------------------------------------------------------------------

def test_conflict_detection_raises_for_divergent_values(monkeypatch, tmp_path):
    """
    Two decisions for same subject with different issued_date must raise ValueError.
    """
    import json, hashlib
    from scripts.review_decisions import (
        ReviewDecision, apply_document_decisions, input_hash
    )
    import scripts.review_decisions as reviews

    sources = [{"source_id": "src:a", "sha256": "a" * 64}]
    document = {"doc_id": "doc:test", "source_ids": ["src:a"], "title": "X", "verification_status": "pending"}
    digest = input_hash(document, {"src:a": sources[0]})

    d1 = ReviewDecision.model_validate({
        "subject_type": "document", "subject_id": "doc:test", "review_type": "metadata",
        "input_sha256": digest, "conclusion": "verified", "evidence_source_id": "src:a",
        "evidence_locator": "header", "reviewer": "rev-A", "reviewed_at": "2026-09-20",
        "values": {"title": "T", "issued_date": "2025-01-01", "valid_from": "2025-02-01"},
    })
    d2 = ReviewDecision.model_validate({
        "subject_type": "document", "subject_id": "doc:test", "review_type": "metadata",
        "input_sha256": digest, "conclusion": "verified", "evidence_source_id": "src:a",
        "evidence_locator": "header", "reviewer": "rev-B", "reviewed_at": "2026-09-20",
        "values": {"title": "T", "issued_date": "2020-01-01", "valid_from": "2020-01-01"},
    })
    monkeypatch.setattr(reviews, "load_decisions", lambda _: [d1, d2])
    with pytest.raises(ValueError, match="Conflicting"):
        apply_document_decisions([document.copy()], sources, tmp_path)


def test_true_duplicates_accepted(monkeypatch, tmp_path):
    """
    Two decisions with identical values/conclusion must succeed silently.
    """
    from scripts.review_decisions import (
        ReviewDecision, apply_document_decisions, input_hash
    )
    import scripts.review_decisions as reviews

    sources = [{"source_id": "src:a", "sha256": "a" * 64}]
    document = {"doc_id": "doc:test", "source_ids": ["src:a"], "title": "X", "verification_status": "pending"}
    digest = input_hash(document, {"src:a": sources[0]})
    base = {
        "subject_type": "document", "subject_id": "doc:test", "review_type": "metadata",
        "input_sha256": digest, "conclusion": "verified", "evidence_source_id": "src:a",
        "evidence_locator": "header", "reviewer": "rev-A", "reviewed_at": "2026-09-20",
        "values": {"title": "T", "issued_date": "2025-01-01", "valid_from": "2025-02-01"},
    }
    monkeypatch.setattr(reviews, "load_decisions", lambda _: [
        ReviewDecision.model_validate(base),
        ReviewDecision.model_validate({**base, "reviewer": "rev-B"}),
    ])
    result = apply_document_decisions([document.copy()], sources, tmp_path)
    assert result[0]["issued_date"] == "2025-01-01"


def test_load_decisions_skips_archive_subdir(tmp_path):
    """
    Files inside archive/ subdirectory must not be loaded by load_decisions.
    """
    import json
    from scripts.review_decisions import load_decisions, ReviewDecision, input_hash

    src_row = {"source_id": "src:a", "sha256": "a" * 64}
    doc_row = {"doc_id": "doc:test", "source_ids": ["src:a"]}
    digest = input_hash(doc_row, {"src:a": src_row})
    decision = {
        "subject_type": "document", "subject_id": "doc:test", "review_type": "metadata",
        "input_sha256": digest, "conclusion": "verified", "evidence_source_id": "src:a",
        "evidence_locator": "header", "reviewer": "auto", "reviewed_at": "2026-09-20",
        "values": {"title": "T", "issued_date": "2020-01-01", "valid_from": "2020-01-01"},
    }
    # Write to archive subdir
    archive = tmp_path / "archive"
    archive.mkdir()
    (archive / "bad.json").write_text(json.dumps(decision), encoding="utf-8")
    # Also write a good one at top level
    good = {**decision, "values": {"title": "T", "issued_date": "2025-01-01", "valid_from": "2025-01-01"}}
    (tmp_path / "good.json").write_text(json.dumps(good), encoding="utf-8")

    loaded = load_decisions(tmp_path)
    assert len(loaded) == 1
    assert loaded[0].values["issued_date"] == "2025-01-01"
