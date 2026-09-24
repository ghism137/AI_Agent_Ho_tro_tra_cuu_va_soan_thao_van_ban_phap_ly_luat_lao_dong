"""Create a reviewable registry from immutable source inventory."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from backend.ingestion.schema import ParsedDocument, Source
from scripts.review_decisions import (
    apply_coverage_decisions,
    apply_document_decisions,
    apply_source_decisions,
    load_review_bindings,
)
from scripts.fetch_official_text import PAGES as OFFICIAL_HTML_PAGES
from scripts.fetch_congbao_corpus import URLS as CONGBAO_URLS


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "reports" / "phase1-implementation" / "inventory.json"
OUT = ROOT / "data" / "registry"
RECONCILIATION = ROOT / "reports" / "phase1-closeout" / "source_reconciliation.json"
NUMBER = re.compile(r"(\d{1,4})[/-](19\d{2}|20\d{2})[/-](QH\d+|NĐ-CP|ND-CP|TT-[A-ZĐ]+|QĐ-TTg)", re.I)
REQUIRED = {
    "labor": ["45/2019/QH14", "145/2020/NĐ-CP", "35/2022/NĐ-CP", "219/2025/NĐ-CP"],
    "social_insurance": ["58/2014/QH13", "41/2024/QH15", "158/2025/NĐ-CP"],
    "health_insurance": ["25/2008/QH12", "51/2024/QH15", "188/2025/NĐ-CP"],
    "unemployment": ["38/2013/QH13", "74/2025/QH15", "374/2025/NĐ-CP"],
    "minimum_wage": ["74/2024/NĐ-CP", "293/2025/NĐ-CP"],
}

OFFICIAL_WORD_URLS = {
    "data/raw/official/Bộ-luật-10-2012-QH13.docx": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=27615",
    "data/raw/official/Bộ-Luật-12-2012-QH13.docx": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=27625",
    "data/raw/official/luât-25-2008-QH12.docx": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=12326",
    "data/raw/official/Luật-38-2013-QH13.docx": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=32912",
    "data/raw/official/Luật-58-2014-QH13.docx": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=46744",
    "data/raw/official/Luật-84-2015-QH13.docx": "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=70811",
}


def apply_registry_reviews(
    sources: list[dict], documents: list[dict], coverage: list[dict],
    *, reviews_dir: Path, bindings_path: Path,
) -> tuple[list[dict], list[dict], list[dict]]:
    bindings = load_review_bindings(bindings_path)
    kwargs = {
        "dependency_fingerprints": bindings.dependency_fingerprints,
        "evidence_content_fingerprints": bindings.source_full_content_sha256,
        "evidence_locator_fingerprints": bindings.locator_sha256,
    }
    sources = apply_source_decisions(sources, reviews_dir, **kwargs)
    documents = apply_document_decisions(documents, sources, reviews_dir, **kwargs)
    coverage = apply_coverage_decisions(coverage, sources, reviews_dir, **kwargs)
    return sources, documents, coverage


def canonical(value: str) -> str | None:
    match = NUMBER.search(value)
    if not match:
        return None
    suffix = match[3].upper().replace('ND-CP', 'NĐ-CP').replace('QĐ-TTG', 'QĐ-TTg')
    return f"{match[1]}/{match[2]}/{suffix}"


def source_document(entry: dict) -> str | None:
    path = Path(entry["path"])
    if path.name in {"Luật Bảo hiểm xã hội 58-2014-QH13.md", "Luật Bảo hiểm xã hội 58-2014-QH13.docx"}:
        return "25/2008/QH12"
    if "Nghị định 152-202-NĐ-CP và phụ lục" in entry["path"]:
        return "152/2020/NĐ-CP"
    if path.name == "Phu luc. Danh muc dia ban ap dung muc luong toi thieu tu ngay 01 thang 7 nam 2024.docx":
        return "74/2024/NĐ-CP"
    if path.name == "Phu luc. Danh muc nghe_cong viec co anh huong xau toi chuc nang sinh san va nuoi con.docx":
        return "10/2020/TT-BLĐTBXH"
    if path.name == "2025_1073 + 1074_219-2025-NĐ-CP.docx":
        return "219/2025/NĐ-CP"
    if path.name == "2025_979 + 980_188-2025-NĐ-CP.docx":
        return "188/2025/NĐ-CP"
    if entry["path"].startswith(("data/raw/hf/", "data/raw/official/")):
        return canonical(path.stem)
    if path.name.lower().startswith(("mau ", "phu ")) or path.name.startswith(("Mau ", "Phu ")):
        return canonical(path.parent.name)
    return canonical(path.stem) or canonical(path.parent.name)


def main() -> None:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    official_urls = {}
    official_urls.update(OFFICIAL_WORD_URLS)
    for number, url in OFFICIAL_HTML_PAGES.items():
        official_urls[f"data/raw/official/{number}.html"] = url
    official_urls["data/raw/official/374-2025-ND-CP-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/180507251028987904/2026/1/27/cong-bao-so-48-ngay-23-01-46946signed-17694874955991619007433.pdf"
    official_urls["data/raw/official/45-2019-QH14-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/CongBao/2019/12/30230/29067-1-993-994.pdf"
    official_urls["data/raw/official/71-2025-QH15-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/CongBao/2025/7/45551/57680-1-965-966.pdf"
    official_urls["data/raw/official/71-2025-QH15.signed.pdf"] = "https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/7/71qh15.signed.pdf"
    official_urls["data/raw/official/113-2025-QH15-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/180507251028987904/2026/1/23/cong-bao-so-35-ngay-21-01-46933signed-17691635381941800021702.pdf"
    official_urls["data/raw/official/124-2025-QH15-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/180507251028987904/2026/1/24/cong-bao-so-36-ngay-21-01-46934signed-17692388704141728786340.pdf"
    official_urls["data/raw/official/73-2025-QH15-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/CongBao/2025/7/45558/57693-1-967-968.pdf"
    official_urls["data/raw/official/84-2025-QH15-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/CongBao/2025/7/45516/57590-1-953-954.pdf"
    official_urls["data/raw/official/142-2025-QH15-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/180507251028987904/2026/1/27/cong-bao-so-44-ngay-22-01-46942signed-1769480518503381294115.pdf"
    official_urls["data/raw/official/162-2026-ND-CP-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/180507251028987904/2026/5/29/cong-bao-so-290-639154061914615919-ngay-29-05-47209_1780017031_signed.pdf"
    official_urls["data/raw/official/61-2020-ND-CP-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2020/5/31455/31418-1-2020635-63661-2020-nd-cp.pdf"
    official_urls["data/raw/official/75-2024-ND-CP-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2024/6/42171/50689-1-2024787-78875-2024-nd-cp.pdf"
    official_urls["data/raw/official/42-2023-ND-CP-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2023/6/39701/45663-1-2023815-81642-2023-nd-cp.pdf"
    official_urls["data/raw/official/108-2021-ND-CP-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2021/12/34934/37803-1-20211043-1044108-2021-nd-cp.pdf"
    official_urls["data/raw/official/44-2019-ND-CP-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2019/5/28999/26822-1-2019457-45844-2019-nd-cp.pdf"
    official_urls["data/raw/official/146-2018-ND-CP-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2018/10/27525/24204-1-20181019-1020146-2018-nd-cp.pdf"
    official_urls["data/raw/official/104-2022-ND-CP-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2022/12/38392/42711-1-2022965-966104-2022-nd-cp.pdf"
    official_urls["data/raw/official/75-2023-ND-CP-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2023/10/40269/46731-1-20231077-107875-2023-nd-cp.pdf"
    official_urls["data/raw/official/74-2025-ND-CP-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2025/3/44712/56002-1-2025655-65674-2025-nd-cp.pdf"
    official_urls["data/raw/official/46-2014-QH13-congbao.pdf"] = "https://congbao.chinhphu.vn/van-ban/luat-so-46-2014-qh13-3045.htm"
    official_urls["data/raw/official/02-2025-ND-CP-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2025/1/43802/54169-1-2025133-13402-2025-nd-cp.pdf"
    official_urls["data/raw/official/70-2015-ND-CP-congbao.pdf"] = "https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-70-2015-nd-cp-16714.htm"
    official_urls["data/raw/official/32-2013-QH13-congbao.pdf"] = "https://congbao.chinhphu.vn/van-ban/luat-so-32-2013-qh13-6394.htm"
    official_urls["data/raw/official/97-2015-QH13-congbao.pdf"] = "https://congbao.chinhphu.vn/van-ban/luat-so-97-2015-qh13-18431.htm"
    official_urls["data/raw/official/35-2018-QH14-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2018/11/27813/24738-1-20181139-114035-2018-qh14.pdf"
    official_urls["data/raw/official/68-2020-QH14-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2020/11/32684/33716-1-20201179-118068-2020-qh14.pdf"
    official_urls["data/raw/official/30-2023-QH15-congbao.pdf"] = "https://congbaocdn.chinhphu.vn/CongBaoCP/VanBan/2023/11/40866/47858-1-202443-4430-2023-qh15.pdf"
    for name, url in CONGBAO_URLS.items():
        official_urls[f"data/raw/official/{name}"] = url
    for name in ("download_manifest.json", "text_download_manifest.json", "p1r04_word_manifest.json"):
        manifest_path = ROOT / "data/raw/official" / name
        if manifest_path.exists():
            for item in json.loads(manifest_path.read_text(encoding="utf-8")):
                official_urls[item["path"]] = item["url"]
    sources = []
    mapping: dict[str, list[str]] = defaultdict(list)
    quarantine = []
    reconciled = {}
    if RECONCILIATION.exists():
        reconciled = {row["path"]: row for row in json.loads(RECONCILIATION.read_text(encoding="utf-8"))["sources"]}
    for entry in inventory["sources"]:
        doc_number = source_document(entry)
        disposition = reconciled.get(entry["path"])
        if disposition and disposition["sha256"] == entry["sha256"] and disposition["disposition"] == "duplicate_derivative_excluded":
            doc_number = disposition["mapped_doc_number"]
        if not doc_number:
            quarantine.append({"source_id": entry["source_id"], "path": entry["path"], "reason": "identity_unresolved"})
        else:
            mapping[doc_number].append(entry["source_id"])
        sources.append(Source.model_validate({
            "source_id": entry["source_id"], "path": entry["path"], "sha256": entry["sha256"],
            "format": entry["format"], "source_url": official_urls.get(entry["path"]), "collected_at": None,
            "verification_status": "pending", "extraction_method": "docx_xml" if entry["format"] == "docx" else "html_dom" if entry["format"] == "html" else "utf8_text" if entry["format"] == "md" else None,
            "source_role": "body" if entry["path"] in OFFICIAL_WORD_URLS else
                           "alternate" if disposition and disposition["sha256"] == entry["sha256"] and disposition["disposition"] == "duplicate_derivative_excluded" else
                           "continuation" if entry["path"].endswith("2025_979 + 980_188-2025-NĐ-CP.docx") else
                           "body_and_forms" if entry["path"].endswith("2025_1073 + 1074_219-2025-NĐ-CP.docx") else None,
        }).model_dump(mode="json"))
    documents = []
    for number, ids in sorted(mapping.items()):
        documents.append(ParsedDocument.model_validate({
            "doc_id": f"doc:{number}", "doc_number": number, "title": number,
            "doc_type": "luat" if "/QH" in number else "nghi_dinh" if "/NĐ-CP" in number else "quyet_dinh" if "/QĐ-" in number else "thong_tu",
            "source_ids": sorted(set(ids)), "verification_status": "pending",
        }).model_dump(mode="json"))
    coverage = []
    for topic, required in REQUIRED.items():
        for number in required:
            coverage.append({"topic": topic, "doc_number": number, "target_as_of": "2026-09-17",
                             "population": "general", "source_present": number in mapping,
                             "verification_status": "pending", "gap": None if number in mapping else "source_missing"})
    sources, documents, coverage = apply_registry_reviews(
        sources, documents, coverage,
        reviews_dir=OUT / "reviews",
        bindings_path=OUT / "review_bindings.json",
    )
    OUT.mkdir(parents=True, exist_ok=True)
    for name, data in (("sources", sources), ("documents", documents), ("coverage", coverage), ("quarantine", quarantine)):
        (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Registry: {len(sources)} sources, {len(documents)} documents, {len(quarantine)} unresolved sources")
    print("Missing required:", ", ".join(item["doc_number"] for item in coverage if not item["source_present"]))


if __name__ == "__main__":
    main()
