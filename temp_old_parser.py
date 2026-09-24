"""Parse legal structure while retaining source locations."""

from __future__ import annotations

import json
import os
import re
import unicodedata
from typing import Any


PART = re.compile(r"^Phß║ºn\s+([IVXLCDM]+|\d+)\b", re.I)
CHAPTER = re.compile(r"^Ch╞░╞íng\s+([IVXLCDM]+|\d+)\b", re.I)
SECTION = re.compile(r"^Mß╗Ñc\s+([IVXLCDM]+|\d+)\b", re.I)
ARTICLE = re.compile(r"^─Éiß╗üu\s+(\d+[a-z]?)(?:\.\s*(.*))?$", re.I)
ANNEX = re.compile(r"^PHß╗ñ Lß╗ñC(?:\s+(?:Sß╗É\s+)?[IVXLCDM\d]+)?$", re.I)
FORM = re.compile(r"^Mß║½u sß╗æ\s+\d+[A-Za-z]?$", re.I)
WATERMARK = re.compile(r"^\s*(?:┬⌐\s*)?(?:www\.)?(?:thuvienphapluat\.vn|luatvietnam\.vn|luatminhkhue\.vn)(?:\s*\|.*)?\s*$", re.I)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text or "")).strip()


def remove_watermarks(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not WATERMARK.fullmatch(line))


def parse_legal_document(
    markdown_content: str,
    doc_meta: dict[str, Any],
    blocks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if blocks is None:
        blocks = [{"kind": "paragraph", "text": line, "locator": f"line:{number}"}
                  for number, line in enumerate(markdown_content.splitlines(), 1)]
    parts: list[dict[str, Any]] = []
    source_tables: list[dict[str, Any]] = []
    for block in blocks:
        if block["kind"] == "table":
            source_tables.append({"locator": block["locator"], "rows": block["rows"],
                                  "cells": block.get("cells", [])})
            for row_number, row in enumerate(block["rows"], 1):
                text = " | ".join(row)
                if text.strip():
                    parts.append({"text": text, "locator": f"{block['locator']}/row:{row_number}",
                                  "kind": "table_row"})
            continue
        else:
            text = normalize_text(block["text"])
        if text and not WATERMARK.fullmatch(text):
            parts.append({"text": text, "locator": block["locator"], "kind": block["kind"]})

    articles: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    hierarchy = {"part": "", "chapter": "", "section": ""}
    content_kind = doc_meta.get("content_kind", "normative")
    annex_count = 0
    pending_heading: str | None = None
    last_normative_number = 0

    def flush() -> None:
        nonlocal current
        if current is not None:
            lines = current.pop("_lines")
            locators = current.pop("source_locators")
            
            CLAUSE = re.compile(r"^(\d+)\.\s")
            POINT = re.compile(r"^([a-z─æ])\)\s", re.I)
            
            base_path = current["structural_path"]
            current_path = list(base_path)
            current_lines = []
            current_locators = []
            
            for line, locator in zip(lines, locators, strict=True):
                clause_match = CLAUSE.match(line)
                point_match = POINT.match(line)
                
                if clause_match:
                    if current_lines:
                        piece = dict(current)
                        piece["structural_path"] = current_path
                        piece["content"] = "\n".join(current_lines)
                        piece["content_segments"] = [{"text": l, "locator": loc} for l, loc in zip(current_lines, current_locators, strict=True)]
                        articles.append(piece)
                    current_path = list(base_path) + [f"item:{clause_match.group(1)}"]
                    current_lines = [line]
                    current_locators = [locator]
                elif point_match:
                    if current_lines:
                        piece = dict(current)
                        piece["structural_path"] = current_path
                        piece["content"] = "\n".join(current_lines)
                        piece["content_segments"] = [{"text": l, "locator": loc} for l, loc in zip(current_lines, current_locators, strict=True)]
                        articles.append(piece)
                    item_part = next((p for p in current_path if p.startswith("item:")), None)
                    if item_part:
                        current_path = list(base_path) + [item_part, f"point:{point_match.group(1).lower()}"]
                    else:
                        current_path = list(base_path) + [f"point:{point_match.group(1).lower()}"]
                    current_lines = [line]
                    current_locators = [locator]
                else:
                    current_lines.append(line)
                    current_locators.append(locator)
                    
            if current_lines:
                piece = dict(current)
                piece["structural_path"] = current_path
                piece["content"] = "\n".join(current_lines)
                piece["content_segments"] = [{"text": l, "locator": loc} for l, loc in zip(current_lines, current_locators, strict=True)]
                articles.append(piece)
            current = None

    for part in parts:
        line = part["text"]
        if pending_heading is not None and part["kind"] == "paragraph":
            if not (PART.match(line) or CHAPTER.match(line) or SECTION.match(line) or ARTICLE.match(line) or ANNEX.match(line)):
                hierarchy[pending_heading] += " " + line
                pending_heading = None
                continue
            pending_heading = None
        if part["kind"] == "paragraph" and (ANNEX.match(line) or
                                           (content_kind in {"annex", "form"} and FORM.match(line))):
            flush()
            annex_count += 1
            content_kind = "form" if FORM.match(line) else "annex"
            current = {"article_number": "ALL", "title": line, "content_kind": content_kind,
                       "structural_path": [content_kind, f"item:{annex_count}"], "hierarchy_path": line,
                       "source_locators": [part["locator"]], "_lines": [line]}
            continue
        if content_kind == "normative" and part["kind"] == "paragraph":
            if PART.match(line):
                flush()
                hierarchy = {"part": line, "chapter": "", "section": ""}
                pending_heading = "part" if re.fullmatch(r"Phß║ºn\s+[IVXLCDM\d]+\.?(?:\s*)", line, re.I) else None
                continue
            if CHAPTER.match(line):
                flush()
                hierarchy["chapter"] = line
                hierarchy["section"] = ""
                pending_heading = "chapter" if re.fullmatch(r"Ch╞░╞íng\s+[IVXLCDM\d]+\.?(?:\s*)", line, re.I) else None
                continue
            if SECTION.match(line):
                flush()
                hierarchy["section"] = line
                pending_heading = "section" if re.fullmatch(r"Mß╗Ñc\s+[IVXLCDM\d]+\.?(?:\s*)", line, re.I) else None
                continue
            match = ARTICLE.match(line)
            if match:
                article_number = int(re.match(r"\d+", match.group(1)).group())
                if article_number > last_normative_number + 1 or article_number < last_normative_number:
                    if current is not None:
                        current["_lines"].append(line)
                        current["source_locators"].append(part["locator"])
                    continue
                flush()
                last_normative_number = article_number
                current = {"article_number": match.group(1), "title": match.group(2) or "",
                           "content_kind": "normative", "structural_path": ["body", f"article:{match.group(1)}"],
                           "hierarchy_path": " > ".join(value for value in hierarchy.values() if value),
                           "source_locators": [part["locator"]], "_lines": [line]}
                continue
        if current is not None:
            current["_lines"].append(line)
            current["source_locators"].append(part["locator"])
    flush()
    if not articles:
        if content_kind not in {"annex", "form"}:
            raise ValueError(f"No articles found in normative document {doc_meta.get('doc_number', '')}")
        articles = [{"article_number": "ALL", "title": parts[0]["text"] if parts else "",
                     "content_kind": content_kind, "structural_path": [content_kind, "item:1"],
                     "hierarchy_path": "", "source_locators": [part["locator"] for part in parts],
                     "content": "\n".join(part["text"] for part in parts),
                     "content_segments": [{"text": part["text"], "locator": part["locator"]} for part in parts]}]
    return {"metadata": doc_meta, "articles": articles, "source_tables": source_tables}


def save_cleaned(cleaned_data: dict[str, Any], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as stream:
        json.dump(cleaned_data, stream, ensure_ascii=False, indent=2)
