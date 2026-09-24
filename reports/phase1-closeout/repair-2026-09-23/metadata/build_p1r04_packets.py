"""Build deterministic P1R-04 metadata proposal packets; never write decisions."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pymupdf
from bs4 import BeautifulSoup
from docx import Document

from backend.ingestion.pdf_text_extractor import extract_pdf_text
from scripts.review_decisions import apply_document_decisions, canonical_hash, content_fingerprint


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
REVIEWS = ROOT / "data/registry/reviews"

PENDING_IDS = [
    "doc:10/2012/QH13", "doc:113/2025/QH15", "doc:12/2012/QH13",
    "doc:124/2025/QH15", "doc:142/2025/QH15", "doc:25/2008/QH12",
    "doc:30/2023/QH15", "doc:32/2013/QH13", "doc:35/2018/QH14",
    "doc:38/2013/QH13", "doc:46/2014/QH13", "doc:51/2024/QH15",
    "doc:58/2014/QH13", "doc:68/2020/QH14", "doc:71/2025/QH15",
    "doc:73/2025/QH15", "doc:74/2025/QH15", "doc:84/2015/QH13",
    "doc:84/2025/QH15", "doc:97/2015/QH13",
]


def pdf_config(source_id, path, title, issued_date, valid_from, title_locs,
               issued_locs, valid_locs, *, note=None, selection_basis="explicit_source_selection"):
    return {
        "source_id": source_id, "path": path, "format": "pdf",
        "proposed_values": {"title": title, "issued_date": issued_date, "valid_from": valid_from},
        "locators": {"title": title_locs, "issued_date": issued_locs, "valid_from": valid_locs},
        "note": note, "selection_basis": selection_basis,
    }


def docx_config(path, title, issued_date, valid_from, title_locs,
                issued_locs, valid_locs, *, note=None):
    return {
        "path": path, "format": "docx",
        "proposed_values": {"title": title, "issued_date": issued_date, "valid_from": valid_from},
        "locators": {"title": title_locs, "issued_date": issued_locs, "valid_from": valid_locs},
        "note": note, "selection_basis": "explicit_source_selection",
    }


CONFIG = {
    "doc:10/2012/QH13": docx_config(
        "data/raw/official/Bộ-luật-10-2012-QH13.docx",
        "Bộ luật Lao động", "2012-06-18", "2013-05-01",
        ["docx/paragraph:3", "docx/paragraph:4"],
        ["docx/paragraph:1376"], ["docx/paragraph:1363"],
    ),
    "doc:12/2012/QH13": docx_config(
        "data/raw/official/Bộ-Luật-12-2012-QH13.docx",
        "Luật Công đoàn", "2012-06-20", "2013-01-01",
        ["docx/paragraph:3", "docx/paragraph:4"],
        ["docx/paragraph:206"], ["docx/paragraph:201"],
    ),
    "doc:25/2008/QH12": docx_config(
        "data/raw/official/luât-25-2008-QH12.docx",
        "Luật Bảo hiểm y tế", "2008-11-14", "2009-07-01",
        ["docx/paragraph:1", "docx/paragraph:2"],
        ["docx/paragraph:411"], ["docx/paragraph:401"],
    ),
    "doc:38/2013/QH13": docx_config(
        "data/raw/official/Luật-38-2013-QH13.docx",
        "Luật Việc làm", "2013-11-16", "2015-01-01",
        ["docx/paragraph:3", "docx/paragraph:4"],
        ["docx/paragraph:395"], ["docx/paragraph:391"],
    ),
    "doc:58/2014/QH13": docx_config(
        "data/raw/official/Luật-58-2014-QH13.docx",
        "Luật Bảo hiểm xã hội", "2014-11-20", "2016-01-01",
        ["docx/paragraph:3", "docx/paragraph:4"],
        ["docx/paragraph:846"], ["docx/paragraph:841"],
        note="General effective date proposed; Article 124(1) has a 2018-01-01 exception for specified Article 2 provisions.",
    ),
    "doc:84/2015/QH13": docx_config(
        "data/raw/official/Luật-84-2015-QH13.docx",
        "Luật An toàn, vệ sinh lao động", "2015-06-25", "2016-07-01",
        ["docx/paragraph:3", "docx/paragraph:4"],
        ["docx/paragraph:769"], ["docx/paragraph:762"],
    ),
    "doc:113/2025/QH15": pdf_config(
        "src:cd968fd5beca988960eae13d17d93f4841c1b12178cfe12d747415355be6d0b6",
        "data/raw/official/113-2025-QH15-congbao.pdf", "Luật Dân số", "2025-12-10", "2026-07-01",
        ["pdf/page:93/line:8", "pdf/page:93/line:9"],
        ["pdf/page:107/line:15", "pdf/page:107/line:16"],
        ["pdf/page:107/line:3", "pdf/page:107/line:5", "pdf/page:107/line:6"],
        note="General effective date proposed; Article 14(c,d) has a 2027-01-01 exception for P1R-06.",
    ),
    "doc:124/2025/QH15": pdf_config(
        "src:102e290a775e86a87d1e1fb4c47c6e1fe06de4ca73de4b9db157302e5146ad87",
        "data/raw/official/124-2025-QH15-congbao.pdf", "Luật Giáo dục nghề nghiệp", "2025-12-10", "2026-01-01",
        ["pdf/page:84/line:8", "pdf/page:84/line:9"],
        ["pdf/page:108/line:10", "pdf/page:108/line:11"],
        ["pdf/page:105/line:30", "pdf/page:105/line:31", "pdf/page:105/line:32"],
        note="General effective date proposed; listed provisions take effect 2026-07-01 and remain for P1R-06.",
    ),
    "doc:142/2025/QH15": pdf_config(
        "src:0b54a605762afb9ac5d22be518652681881ba1e528c94ec514b8cbfb1af33bf3",
        "data/raw/official/142-2025-QH15-congbao.pdf", "Luật Phục hồi, phá sản", "2025-12-11", "2026-03-01",
        ["pdf/page:41/line:10", "pdf/page:41/line:11"],
        ["pdf/page:100/line:29", "pdf/page:100/line:30"],
        ["pdf/page:100/line:3", "pdf/page:100/line:4", "pdf/page:100/line:5", "pdf/page:100/line:6"],
        note="General effective date proposed; Article 38(3) takes effect 2026-07-01 and remains for P1R-06.",
    ),
    "doc:30/2023/QH15": pdf_config(
        "src:a07a8f30112e0308759f6521f9b16356e0df03a7e8cd5724fffa9402450b2d7d",
        "data/raw/official/30-2023-QH15-congbao.pdf",
        "Luật Lực lượng tham gia bảo vệ an ninh, trật tự ở cơ sở", "2023-11-28", "2024-07-01",
        ["pdf/page:1/line:7", "pdf/page:1/line:8"],
        ["pdf/page:17/line:12", "pdf/page:17/line:13"],
        ["pdf/page:17/line:6", "pdf/page:17/line:7"],
    ),
    "doc:32/2013/QH13": pdf_config(
        "src:f793405496cf4efd631b3e87ad9bef489598c934ef75a7712ce3db4e77a1b756",
        "data/raw/official/32-2013-QH13-congbao.pdf",
        "Luật sửa đổi, bổ sung một số điều của Luật Thuế thu nhập doanh nghiệp", "2013-06-19", "2014-01-01",
        ["pdf/page:1/line:15", "pdf/page:1/line:16", "pdf/page:1/line:17"],
        ["pdf/page:11/line:16", "pdf/page:11/line:17"],
        ["pdf/page:10/line:6", "pdf/page:10/line:7", "pdf/page:10/line:8"],
    ),
    "doc:35/2018/QH14": pdf_config(
        "src:abdcbb3eed2152c7a51a4827ffc32210a76757b2625f59a4b4c9f1908dd716fe",
        "data/raw/official/35-2018-QH14-congbao.pdf",
        "Luật sửa đổi, bổ sung một số điều của 37 luật có liên quan đến quy hoạch", "2018-11-20", "2019-01-01",
        ["pdf/page:1/line:12", "pdf/page:1/line:13", "pdf/page:1/line:14"],
        ["pdf/page:77/line:24", "pdf/page:77/line:25"],
        ["pdf/page:77/line:20", "pdf/page:77/line:21"],
    ),
    "doc:46/2014/QH13": pdf_config(
        "src:9dd7d62ec6b461f31fea4e5fbf2fb47d119dfe1ebdbe354a27c4b79311216f28",
        "data/raw/official/46-2014-QH13-congbao.pdf",
        "Luật sửa đổi, bổ sung một số điều của Luật Bảo hiểm y tế", "2014-06-13", "2015-01-01",
        ["pdf/page:1/line:13", "pdf/page:1/line:14"],
        ["pdf/page:14/line:20", "pdf/page:14/line:21"],
        ["pdf/page:14/line:15", "pdf/page:14/line:16"],
    ),
    "doc:51/2024/QH15": {
        "source_id": "src:b4bee6916e931a5e97926dc672d26f90ad42199ba380ae94a3d81bca7f9a8419",
        "path": "data/raw/official/51-2024-QH15.html", "format": "html",
        "proposed_values": {
            "title": "Luật sửa đổi, bổ sung một số điều của Luật Bảo hiểm y tế",
            "issued_date": "2024-11-27", "valid_from": "2025-07-01",
        },
        "locators": {
            "title": ["html/articleBody/node:10", "html/articleBody/node:11"],
            "issued_date": ["html/articleBody/node:336"],
            "valid_from": ["html/articleBody/node:325"],
        },
        "note": "General effective date proposed; multiple provisions apply from 2025-01-01 and remain for P1R-06.",
        "selection_basis": "single official source in document source_ids",
    },
    "doc:68/2020/QH14": pdf_config(
        "src:1758c50b526766cdc11241742a629040cd4cc0530b63c61e7d23903cf1717fc9",
        "data/raw/official/68-2020-QH14-congbao.pdf", "Luật Cư trú", "2020-11-13", "2021-07-01",
        ["pdf/page:1/line:14", "pdf/page:1/line:15"],
        ["pdf/page:27/line:14", "pdf/page:27/line:15"],
        ["pdf/page:26/line:30", "pdf/page:26/line:32"],
    ),
    "doc:71/2025/QH15": pdf_config(
        "src:b79d8a86c8a7c7d8046421f1db78404f079cf8e231d7081f60a3822494994e20",
        "data/raw/official/71-2025-QH15-congbao.pdf", "Luật Công nghiệp công nghệ số", "2025-06-14", "2026-01-01",
        ["pdf/page:39/line:14", "pdf/page:39/line:15"],
        ["pdf/page:69/line:32", "pdf/page:69/line:33"],
        ["pdf/page:69/line:10", "pdf/page:69/line:11", "pdf/page:69/line:12", "pdf/page:69/line:13", "pdf/page:69/line:14"],
        note="General effective date proposed; Articles 11, 28 and 29 took effect 2025-07-01. Signed scan retained as alternate.",
    ),
    "doc:73/2025/QH15": pdf_config(
        "src:26282fec0c5ce13d2543ba23cc24e69d12ff3716c46195403241ec838d87fb9b",
        "data/raw/official/73-2025-QH15-congbao.pdf", "Luật Nhà giáo", "2025-06-16", "2026-01-01",
        ["pdf/page:57/line:12", "pdf/page:57/line:13"],
        ["pdf/page:75/line:33", "pdf/page:75/line:34"],
        ["pdf/page:75/line:20", "pdf/page:75/line:21"],
    ),
    "doc:74/2025/QH15": pdf_config(
        "src:a3c5cb151d13aa6475f3389ba25eae7206762552443ae1df4a3667e93edb3a17",
        "data/raw/official/74-2025-QH15-congbao.pdf", "Luật Việc làm", "2025-06-16", "2026-01-01",
        ["pdf/page:29/line:13"],
        ["pdf/page:55/line:34", "pdf/page:55/line:35"],
        ["pdf/page:55/line:12", "pdf/page:55/line:13"],
        note="Gazette text layer is canonical proposal source; signed PDF is scan-only and HTML is an alternate.",
        selection_basis="official Gazette source in document source_ids; explicit source_selection entry absent",
    ),
    "doc:84/2025/QH15": pdf_config(
        "src:a198c491fb634a142b42ae562024a14012c85340eaa12742795b69db37bd8930",
        "data/raw/official/84-2025-QH15-congbao.pdf", "Luật Thanh tra", "2025-06-25", "2025-07-01",
        ["pdf/page:4/line:13", "pdf/page:4/line:14"],
        ["pdf/page:44/line:31", "pdf/page:44/line:32"],
        ["pdf/page:43/line:28", "pdf/page:43/line:29"],
    ),
    "doc:97/2015/QH13": pdf_config(
        "src:81da25dc6b04639a1043f35e275228c9aa455b87dbfb8dde8b81ecebb49224b2",
        "data/raw/official/97-2015-QH13-congbao.pdf", "Luật Phí và lệ phí", "2015-11-25", "2017-01-01",
        ["pdf/page:1/line:13", "pdf/page:1/line:14"],
        ["pdf/page:7/line:22", "pdf/page:7/line:23"],
        ["pdf/page:6/line:25", "pdf/page:6/line:26"],
    ),
}


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def html_blocks(path):
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    body = soup.select_one("[itemprop=articleBody]")
    if body is None:
        raise ValueError(f"articleBody missing from {path}")
    result = []
    for index, node in enumerate(body.find_all(["h2", "h4", "p", "td"]), 1):
        text = " ".join(node.get_text(" ", strip=True).split())
        if text and (not result or result[-1]["text"] != text):
            result.append({"locator": f"html/articleBody/node:{index}", "text": text})
    return result


def source_blocks(config):
    path = ROOT / config["path"]
    if config["format"] == "html":
        return html_blocks(path)
    if config["format"] == "docx":
        return [
            {"locator": f"docx/paragraph:{index}", "text": " ".join(paragraph.text.split())}
            for index, paragraph in enumerate(Document(path).paragraphs, 1)
            if " ".join(paragraph.text.split())
        ]
    document = pymupdf.open(path)
    return [
        {"locator": item["locator"], "text": " ".join(item["text"].split())}
        for item in extract_pdf_text(path, first_page=1, last_page=len(document))
    ]


def evidence_item(field, locators, by_locator, full_content_sha256, source):
    missing = [locator for locator in locators if locator not in by_locator]
    if missing:
        raise ValueError(f"Missing locators for {field}: {missing}")
    text = "\n".join(by_locator[locator] for locator in locators)
    prefix, start = locators[0].rsplit(":", 1)
    same_prefix = all(locator.rsplit(":", 1)[0] == prefix for locator in locators)
    numbers = [int(locator.rsplit(":", 1)[1]) for locator in locators]
    contiguous = numbers == list(range(numbers[0], numbers[0] + len(numbers)))
    if len(locators) == 1:
        locator = locators[0]
    elif same_prefix and contiguous:
        locator = f"{prefix}:{start}-{numbers[-1]}"
    else:
        locator = "+".join(locators)
    return {
        "field": field,
        "source_id": source["source_id"],
        "source_sha256": source["sha256"],
        "full_content_sha256": full_content_sha256,
        "locator": locator,
        "locator_sha256": canonical_hash(text),
        "text": text,
    }


def main():
    documents = load_json("data/registry/documents.json")
    sources = load_json("data/registry/sources.json")
    selections = load_json("data/registry/source_selection.json")
    evidence = load_json("reports/phase1-review-2026-09-23/evidence.json")
    by_doc = {row["doc_id"]: row for row in documents}
    by_source = {row["source_id"]: row for row in sources}
    if evidence["metadata"]["pending_ids"] != PENDING_IDS:
        raise ValueError("P1R-04 pending ID order differs from pinned 23/09 evidence")

    records = []
    for doc_id in PENDING_IDS:
        document = by_doc[doc_id]
        config = CONFIG.get(doc_id)
        if config is None:
            listed = [by_source[source_id] for source_id in document["source_ids"]]
            if any(row["path"].startswith("data/raw/official/") for row in listed):
                raise ValueError(f"Unclassified official source for {doc_id}")
            records.append({
                "doc_id": doc_id,
                "disposition": "PENDING_BLOCKED_MISSING_SELECTED_OFFICIAL_SOURCE",
                "proposed_values": None,
                "listed_sources": [
                    {"source_id": row["source_id"], "path": row["path"], "format": row["format"],
                     "source_sha256": row["sha256"]}
                    for row in listed
                ],
                "explicit_source_selection": selections.get(doc_id),
                "reason": "No usable official source is selected in the current document inputs; filename/generated metadata was not used.",
            })
            continue

        if config["format"] == "docx":
            selected = selections.get(doc_id)
            if not selected or selected.get("body") != config["path"]:
                raise ValueError(f"Configured DOCX is not explicitly selected for {doc_id}")
            candidates = [row for row in sources if row["path"] == config["path"]]
            if len(candidates) != 1:
                raise ValueError(f"Expected one registered source for {config['path']}")
            source = candidates[0]
        else:
            source = by_source[config["source_id"]]
        if source["path"] != config["path"] or source["source_id"] not in document["source_ids"]:
            raise ValueError(f"Configured source is not bound to {doc_id}")
        actual_hash = file_hash(ROOT / source["path"])
        if actual_hash != source["sha256"]:
            raise ValueError(f"Source bytes changed for {source['path']}")
        blocks = source_blocks(config)
        full_content_sha256 = canonical_hash(blocks)
        by_locator = {item["locator"]: item["text"] for item in blocks}
        field_evidence = [
            evidence_item(field, config["locators"][field], by_locator, full_content_sha256, source)
            for field in ("title", "issued_date", "valid_from")
        ]
        records.append({
            "doc_id": doc_id,
            "disposition": "PROPOSED_AWAITING_INDEPENDENT_REVIEW",
            "selection_basis": config["selection_basis"],
            "source": {
                "source_id": source["source_id"], "path": source["path"],
                "source_url": source.get("source_url"), "source_sha256": source["sha256"],
                "full_content_sha256": full_content_sha256,
            },
            "subject_input_fingerprint_without_review_dependencies": content_fingerprint(
                document, by_source, {}
            ),
            "proposed_values": config["proposed_values"],
            "evidence": field_evidence,
            "conflicts_or_alternates": config.get("note"),
            "explicit_source_selection": selections.get(doc_id),
        })

    diagnostics = []
    neutral = copy.deepcopy(documents)
    for row in neutral:
        row["verification_status"] = "pending"
    reconciled = apply_document_decisions(neutral, sources, REVIEWS, diagnostics=diagnostics)
    counts = {}
    for row in reconciled:
        status = row.get("verification_status", "pending")
        counts[status] = counts.get(status, 0) + 1

    for index in range(0, len(records), 5):
        batch = records[index:index + 5]
        payload = {
            "task_id": "P1R-04", "batch": index // 5 + 1,
            "status": "BUILDER_PROPOSALS_COMPLETE_AWAITING_REVIEW",
            "document_count": len(batch), "documents": batch,
        }
        (OUT / f"batch-{index // 5 + 1:02d}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    summary = {
        "task_id": "P1R-04",
        "status": "BUILDER_DONE_AWAITING_SOURCE_REVIEW",
        "pending_ids_sha256": canonical_hash(PENDING_IDS),
        "input_hashes": {
            path: file_hash(ROOT / path)
            for path in (
                "data/registry/documents.json", "data/registry/sources.json",
                "data/registry/source_selection.json",
                "data/registry/reviews/archive/ARCHIVE_MANIFEST.json",
                "reports/phase1-review-2026-09-23/evidence.json",
            )
        },
        "batch_files": [f"batch-{number:02d}.json" for number in range(1, 5)],
        "dispositions": {
            "proposed_awaiting_independent_review": sum(r["disposition"].startswith("PROPOSED") for r in records),
            "pending_missing_selected_official_source": sum(r["disposition"].startswith("PENDING") for r in records),
        },
        "active_review_reconciliation": {
            "status_counts_after_neutral_replay": counts,
            "diagnostics": diagnostics,
            "active_review_files": len(list(REVIEWS.glob("*.json"))),
        },
        "hash_convention": {
            "full_content_sha256": "canonical_hash of ordered normalized locator/text blocks for the complete selected source",
            "locator_sha256": "canonical_hash of newline-joined exact normalized text at the recorded locator(s)",
        },
        "registry_decisions_written": 0,
    }
    (OUT / "evidence-index.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
