"""Markdown report generation for Phoenix-RCA legal and executive audiences."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_KEYS = (
    "incident_timestamp",
    "root_cause_technical",
    "business_blast_radius",
    "jury_translation_plain_english",
)

DEFAULT_REPORT_PATH = "PHOENIX_RCA_REPORT.md"


def generate_legal_report(
    ai_analysis: str | Mapping[str, Any],
    output_path: str | Path = DEFAULT_REPORT_PATH,
) -> Path:
    """Generate a readable Markdown RCA report from analyzer JSON output."""

    analysis = _parse_analysis(ai_analysis)
    destination = Path(output_path)
    if destination.parent != Path("."):
        destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(_render_markdown(analysis), encoding="utf-8")
    return destination


def _parse_analysis(ai_analysis: str | Mapping[str, Any]) -> dict[str, str]:
    if isinstance(ai_analysis, Mapping):
        parsed = dict(ai_analysis)
    elif isinstance(ai_analysis, str):
        parsed = _load_json_object(ai_analysis)
    else:
        raise TypeError("ai_analysis must be a JSON string or mapping")

    missing = [key for key in EXPECTED_KEYS if key not in parsed]
    if missing:
        raise ValueError(f"AI analysis missing required keys: {missing}")

    return {
        key: _normalize_markdown_value(parsed.get(key))
        for key in EXPECTED_KEYS
    }


def _load_json_object(raw_json: str) -> dict[str, Any]:
    text = _strip_markdown_fence(raw_json)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("AI analysis is not valid JSON.") from None
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError("AI analysis is not valid JSON.") from exc

    if not isinstance(parsed, dict):
        raise ValueError("AI analysis JSON must be an object.")
    return parsed


def _render_markdown(analysis: Mapping[str, str]) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    timestamp = analysis["incident_timestamp"]
    root_cause = analysis["root_cause_technical"]
    blast_radius = analysis["business_blast_radius"]
    plain_english = analysis["jury_translation_plain_english"]
    plain_english_quote = _blockquote(plain_english)

    return f"""# PHOENIX-RCA REPORT

**Automated Technical Root-Cause Analysis & Evidence Discovery Platform**

**Report Generated:** {generated_at}

---

## 1. Executive Finding

{_blockquote(f"**Plain-English Summary:** {plain_english}")}

## 2. Incident Timestamp

**Best-Supported Time of Incident:** `{timestamp}`

## 3. Technical Root Cause

**Engineering Determination:**

{root_cause}

## 4. Business Blast Radius

**Operational and Legal Relevance:**

{blast_radius}

## 5. Courtroom-Ready Explanation

{plain_english_quote}

## 6. Evidence Handling Notes

**Compliance Controls Applied:** Source logs were masked before model analysis. IP
addresses and credential-bearing database connection strings should appear only as
`[REDACTED_IP]` and `[REDACTED_CREDENTIAL]` markers in downstream artifacts.

**Reliability Note:** This report is generated from the evidence supplied to the
analyzer. Final legal conclusions should be cross-checked against source systems,
change records, incident tickets, and witness testimony.
"""


def _normalize_markdown_value(value: Any) -> str:
    if value is None:
        return "Unknown."
    if isinstance(value, str):
        return value.strip() or "Unknown."
    return json.dumps(value, ensure_ascii=False)


def _blockquote(text: str) -> str:
    lines = text.splitlines() or [text]
    return "\n".join(f"> {line}" if line else ">" for line in lines)


def _strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()
