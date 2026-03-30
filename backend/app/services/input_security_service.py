from __future__ import annotations

import re
import unicodedata

PROMPT_INJECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "ignore_instructions": re.compile(
        r"ignore\s+(all|any|previous|above)?\s*instructions",
        re.IGNORECASE,
    ),
    "override_system": re.compile(r"system\s*prompt|developer\s*message", re.IGNORECASE),
    "tool_abuse": re.compile(r"tool\s*call|function\s*call|execute\s+command", re.IGNORECASE),
    "jailbreak": re.compile(r"jailbreak|do\s*anything\s*now|bypass\s*safety", re.IGNORECASE),
}


def normalize_untrusted_text(value: str, max_length: int = 20_000) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    safe_chars = []
    for char in normalized:
        code = ord(char)
        if char in {"\n", "\t", "\r"} or code >= 32:
            safe_chars.append(char)

    compact = "".join(safe_chars).strip()
    return compact[:max_length]


def detect_prompt_injection_signals(value: str) -> list[str]:
    signals: list[str] = []
    for name, pattern in PROMPT_INJECTION_PATTERNS.items():
        if pattern.search(value):
            signals.append(name)
    return signals


def strip_prompt_injection_content(value: str) -> tuple[str, list[str]]:
    signals = detect_prompt_injection_signals(value)
    if not signals:
        return value, []

    clean_lines: list[str] = []
    removed: list[str] = []

    for line in value.splitlines():
        line_signals = detect_prompt_injection_signals(line)
        if line_signals:
            removed.extend(line_signals)
            continue
        clean_lines.append(line)

    dedup_removed = sorted(set(removed if removed else signals))
    return "\n".join(clean_lines).strip(), dedup_removed


def sanitize_label(value: str, max_length: int = 255) -> str:
    return normalize_untrusted_text(value.replace("\n", " "), max_length=max_length)


def sanitize_string_list(
    items: list[str],
    max_items: int = 30,
    max_length: int = 64,
) -> list[str]:
    cleaned: list[str] = []
    for item in items:
        normalized = sanitize_label(item, max_length=max_length)
        if normalized:
            cleaned.append(normalized)
    # preserve order while deduplicating
    seen: set[str] = set()
    result: list[str] = []
    for value in cleaned:
        lowered = value.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        result.append(value)
        if len(result) >= max_items:
            break
    return result
