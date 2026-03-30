from __future__ import annotations

import re
from io import BytesIO

from docx import Document
from pypdf import PdfReader

from app.services.input_security_service import (
    normalize_untrusted_text,
    strip_prompt_injection_content,
)

SKILL_KEYWORDS = {
    "python",
    "fastapi",
    "django",
    "flask",
    "sql",
    "postgresql",
    "typescript",
    "javascript",
    "react",
    "next.js",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "scikit-learn",
    "pandas",
    "numpy",
    "tensorflow",
}

LANGUAGE_KEYWORDS = {
    "francais": "fr",
    "français": "fr",
    "english": "en",
    "anglais": "en",
    "espagnol": "es",
    "spanish": "es",
    "allemand": "de",
    "german": "de",
}

KNOWN_LOCATIONS = {
    "paris",
    "lyon",
    "lille",
    "toulouse",
    "marseille",
    "nantes",
    "bordeaux",
    "rennes",
    "remote",
    "hybride",
}


def extract_text_from_document(filename: str, content: bytes) -> str:
    lower_name = filename.lower()

    if lower_name.endswith(".pdf"):
        reader = PdfReader(BytesIO(content))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()

    if lower_name.endswith(".docx"):
        document = Document(BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()

    return content.decode("utf-8", errors="ignore").strip()


def estimate_seniority(raw_text: str) -> str | None:
    years = [
        int(match)
        for match in re.findall(r"(\d{1,2})\s*(?:ans|an|years|year)", raw_text.lower())
    ]
    if not years:
        return None

    max_years = max(years)
    if max_years <= 2:
        return "junior"
    if max_years <= 5:
        return "mid"
    if max_years <= 8:
        return "senior"
    return "lead"


def parse_profile_document(filename: str, content: bytes) -> dict[str, object]:
    extracted_text = extract_text_from_document(filename, content)
    normalized_text = normalize_untrusted_text(extracted_text, max_length=50_000)
    safe_text, security_flags = strip_prompt_injection_content(normalized_text)
    lowered = safe_text.lower()

    skills = sorted(skill for skill in SKILL_KEYWORDS if skill in lowered)
    languages = sorted({code for keyword, code in LANGUAGE_KEYWORDS.items() if keyword in lowered})

    location = next((loc for loc in KNOWN_LOCATIONS if loc in lowered), None)
    seniority = estimate_seniority(safe_text)

    guessed_name = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").strip().title()

    return {
        "full_name": guessed_name or "Unknown Candidate",
        "raw_text": safe_text,
        "parsed_skills": skills,
        "parsed_languages": languages,
        "parsed_location": location,
        "parsed_seniority": seniority,
        "security_flags": security_flags,
    }
