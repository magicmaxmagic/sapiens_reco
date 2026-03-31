from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from faker import Faker
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


@dataclass(frozen=True)
class GenerationConfig:
    seed: int = 42
    min_profiles: int = 300
    max_profiles: int = 500
    min_missions: int = 50
    max_missions: int = 100
    top_k: int = 10


@dataclass(frozen=True)
class ProfileView:
    profile_id: int
    full_name: str
    title: str
    seniority: str
    location: str
    language: str
    availability_days: int
    years_experience: int
    daily_rate: float
    primary_domain: str
    sectors: set[str]
    skills: set[str]
    cv_text: str


@dataclass(frozen=True)
class MissionView:
    mission_id: int
    title: str
    description: str
    required_seniority: str
    required_location: str
    required_language: str
    required_skills: set[str]
    sector: str
    desired_start_in_days: int
    duration_months: int
    max_daily_rate: float
    priority: str
    inferred_domain: str


SENIORITY_META: dict[str, dict[str, int]] = {
    "Junior": {"rank": 0, "years_min": 1, "years_max": 3, "rate_min": 350, "rate_max": 550},
    "Confirmed": {"rank": 1, "years_min": 3, "years_max": 6, "rate_min": 550, "rate_max": 800},
    "Senior": {"rank": 2, "years_min": 7, "years_max": 11, "rate_min": 800, "rate_max": 1150},
    "Expert": {"rank": 3, "years_min": 12, "years_max": 20, "rate_min": 1150, "rate_max": 1600},
}

RANK_TO_SENIORITY = {
    values["rank"]: seniority for seniority, values in SENIORITY_META.items()
}

LOCATIONS = ["Paris", "Lyon", "Lille", "Toulouse", "Nantes", "Bruxelles", "Montreal", "Remote"]
LANGUAGES = ["Francais", "Anglais", "Bilingue"]
SECTORS = ["Banque", "Assurance", "Retail", "Industrie", "Energie", "Public", "Telecom", "Sante"]
SOURCES = ["CV PDF", "CV Word", "ATS", "Referral", "LinkedIn", "Email"]

AVAILABILITY_TO_DAYS = {
    "ASAP": 0,
    "In 15 days": 15,
    "In 30 days": 30,
    "In 60 days": 60,
    "Later": 90,
}

DOMAINS = ["Data / IA", "Cyber", "Digital", "Cloud", "ERP", "CRM", "DevOps"]
DOMAIN_WEIGHTS = np.array([0.24, 0.13, 0.14, 0.16, 0.10, 0.09, 0.14])

DOMAIN_SKILLS: dict[str, list[str]] = {
    "Data / IA": [
        "Python",
        "SQL",
        "Spark",
        "Databricks",
        "Snowflake",
        "dbt",
        "Airflow",
        "Power BI",
        "Tableau",
        "NLP",
        "MLOps",
        "FastAPI",
    ],
    "Cyber": ["IAM", "SIEM", "SOC", "Python", "Azure", "AWS", "GCP", "Terraform", "SQL"],
    "Digital": ["React", "Java", "C#", "FastAPI", "Python", "SQL", "Docker", "Tableau"],
    "Cloud": ["AWS", "Azure", "GCP", "Terraform", "Kubernetes", "Docker", "DevOps", "Python"],
    "ERP": ["SAP", "SQL", "Power BI", "Python", "Airflow", "Snowflake"],
    "CRM": ["Salesforce", "SQL", "Java", "C#", "Power BI", "Python"],
    "DevOps": ["DevOps", "Docker", "Kubernetes", "Terraform", "AWS", "Azure", "GCP", "Python"],
}

DOMAIN_TITLES: dict[str, list[str]] = {
    "Data / IA": ["Data Engineer", "Data Scientist", "ML Engineer", "Data Analyst"],
    "Cyber": ["Consultant Cyber", "Analyste SOC", "Expert IAM", "Architecte Cyber"],
    "Digital": ["Consultant Digital", "Full Stack Engineer", "Lead Developer", "Product Analyst"],
    "Cloud": ["Cloud Engineer", "Architecte Cloud", "Consultant Cloud", "Platform Engineer"],
    "ERP": ["Consultant SAP", "Expert ERP", "Business Analyst ERP", "Tech Lead ERP"],
    "CRM": ["Consultant Salesforce", "Expert CRM", "CRM Analyst", "CRM Solution Engineer"],
    "DevOps": ["DevOps Engineer", "SRE", "Platform DevOps", "Lead DevOps"],
}

MISSION_ROLES: dict[str, list[str]] = {
    "Data / IA": ["Data Engineer", "Data Analyst", "ML Engineer", "Lead Data Scientist"],
    "Cyber": ["Consultant Cyber IAM", "Analyste SOC", "Expert SIEM", "Architecte Cyber"],
    "Digital": ["Product Analyst", "Developer React", "Tech Lead Digital", "Consultant Digital"],
    "Cloud": ["Cloud Engineer", "Architecte Cloud", "Consultant AWS", "Consultant Azure"],
    "ERP": ["Consultant SAP", "Chef de projet ERP", "Expert ERP", "Business Analyst ERP"],
    "CRM": ["Consultant Salesforce", "Consultant CRM", "Tech Lead CRM", "CRM Analyst"],
    "DevOps": ["DevOps Cloud", "SRE", "Platform Engineer", "DevOps Kubernetes"],
}

ALL_SKILLS = sorted({skill for values in DOMAIN_SKILLS.values() for skill in values})

CRITICAL_SKILLS = {
    "Python",
    "SQL",
    "AWS",
    "Azure",
    "GCP",
    "Power BI",
    "Spark",
    "Databricks",
    "Docker",
    "Kubernetes",
    "NLP",
    "MLOps",
    "IAM",
    "SIEM",
    "SOC",
    "SAP",
    "Salesforce",
    "Terraform",
}

FRENCH_CITIES = {"Paris", "Lyon", "Lille", "Toulouse", "Nantes"}


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def to_pipe_list(items: list[str]) -> str:
    return " | ".join(items)


def from_pipe_list(value: Any) -> list[str]:
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).split("|") if part.strip()]


def normalize_text(value: str) -> str:
    return " ".join(value.lower().strip().split())


def weighted_choice(rng: np.random.Generator, values: list[str], probs: np.ndarray) -> str:
    return str(rng.choice(values, p=probs / probs.sum()))


def allocate_months(
    total_months: int,
    parts: int,
    rng: np.random.Generator,
    minimum: int = 6,
) -> list[int]:
    total_months = max(total_months, parts * minimum)
    base = np.full(parts, minimum, dtype=int)
    remaining = total_months - int(base.sum())
    if remaining > 0:
        weights = rng.dirichlet(np.ones(parts))
        allocation = np.floor(weights * remaining).astype(int)
        base += allocation
        rest = remaining - int(allocation.sum())
        if rest > 0:
            indices = rng.choice(np.arange(parts), size=rest, replace=True)
            for idx in indices:
                base[idx] += 1
    return base.tolist()


def infer_domain(required_skills: set[str]) -> str:
    best_domain = "Digital"
    best_overlap = -1
    for domain, domain_skills in DOMAIN_SKILLS.items():
        overlap = len(required_skills.intersection(domain_skills))
        if overlap > best_overlap:
            best_overlap = overlap
            best_domain = domain
    return best_domain


def compute_daily_rate(seniority: str, domain: str, rng: np.random.Generator) -> int:
    meta = SENIORITY_META[seniority]
    base = int(rng.integers(meta["rate_min"], meta["rate_max"] + 1))
    domain_bonus = {
        "Data / IA": 70,
        "Cyber": 100,
        "Digital": 20,
        "Cloud": 80,
        "ERP": 40,
        "CRM": 25,
        "DevOps": 60,
    }[domain]
    return max(300, base + domain_bonus + int(rng.integers(-30, 31)))


def mission_budget(required_seniority: str, domain: str, rng: np.random.Generator) -> int:
    base_ranges = {
        "Junior": (550, 700),
        "Confirmed": (750, 950),
        "Senior": (1000, 1300),
        "Expert": (1300, 1700),
    }
    low, high = base_ranges[required_seniority]
    domain_adj = {
        "Data / IA": 50,
        "Cyber": 90,
        "Digital": 10,
        "Cloud": 70,
        "ERP": 40,
        "CRM": 20,
        "DevOps": 55,
    }[domain]
    return int(rng.integers(low, high + 1) + domain_adj + rng.integers(-25, 26))


def build_cv_text(
    title: str,
    years_experience: int,
    domain: str,
    skills: list[str],
    sectors: list[str],
    language: str,
    location: str,
    fake: Faker,
) -> str:
    notable_clients = f"{fake.company()} et {fake.company()}"
    return (
        f"{title} avec {years_experience} ans d'experience en {domain}. "
        f"Competences cles: {', '.join(skills[:5])}. "
        f"Interventions dans les secteurs {', '.join(sectors)}. "
        f"Missions notables pour {notable_clients}. "
        f"Langues: {language}. Localisation: {location}."
    )


def generate_profiles(
    n_profiles: int,
    rng: np.random.Generator,
    fake: Faker,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    seniority_probs = np.array([0.18, 0.36, 0.30, 0.16])
    location_probs = np.array([0.24, 0.12, 0.08, 0.10, 0.08, 0.10, 0.07, 0.21])
    language_base = np.array([0.45, 0.20, 0.35])

    for profile_id in range(1, n_profiles + 1):
        domain = weighted_choice(rng, DOMAINS, DOMAIN_WEIGHTS)
        seniority = weighted_choice(rng, list(SENIORITY_META.keys()), seniority_probs)
        location = weighted_choice(rng, LOCATIONS, location_probs)

        language_probs = language_base
        if location in {"Bruxelles", "Montreal", "Remote"}:
            language_probs = np.array([0.25, 0.15, 0.60])
        language = weighted_choice(rng, LANGUAGES, language_probs)

        years_experience = int(
            rng.integers(
                SENIORITY_META[seniority]["years_min"],
                SENIORITY_META[seniority]["years_max"] + 1,
            )
        )

        availability_status = weighted_choice(
            rng,
            list(AVAILABILITY_TO_DAYS.keys()),
            np.array([0.18, 0.24, 0.28, 0.18, 0.12]),
        )
        base_days = AVAILABILITY_TO_DAYS[availability_status]
        jitter = (
            int(rng.integers(0, 6))
            if availability_status != "Later"
            else int(rng.integers(0, 45))
        )
        availability_days = max(0, base_days + jitter)

        daily_rate = compute_daily_rate(seniority, domain, rng)

        domain_skills = DOMAIN_SKILLS[domain]
        core_count = int(rng.integers(4, min(8, len(domain_skills)) + 1))
        core_skills = list(rng.choice(domain_skills, size=core_count, replace=False))

        extra_pool = [skill for skill in ALL_SKILLS if skill not in core_skills]
        extra_count = int(rng.integers(1, 4))
        extra_skills = list(rng.choice(extra_pool, size=extra_count, replace=False))
        skills = sorted(set(core_skills + extra_skills))

        sector_count = int(rng.integers(1, 4))
        sectors = sorted(list(rng.choice(SECTORS, size=sector_count, replace=False)))

        role = str(rng.choice(DOMAIN_TITLES[domain]))
        title = f"{role} {seniority}"

        created_at = (
            datetime.now(timezone.utc) - timedelta(days=int(rng.integers(0, 720)))
        ).replace(microsecond=0).isoformat()

        records.append(
            {
                "profile_id": profile_id,
                "full_name": fake.name(),
                "title": title,
                "seniority": seniority,
                "location": location,
                "languages": language,
                "availability_status": availability_status,
                "availability_days": availability_days,
                "years_experience": years_experience,
                "daily_rate": daily_rate,
                "primary_domain": domain,
                "sectors": to_pipe_list(sectors),
                "skills": to_pipe_list(skills),
                "source": str(rng.choice(SOURCES)),
                "cv_text": build_cv_text(
                    title,
                    years_experience,
                    domain,
                    skills,
                    sectors,
                    language,
                    location,
                    fake,
                ),
                "created_at": created_at,
            }
        )

    return pd.DataFrame(records)


def generate_experiences(profiles_df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    experience_id = 1
    today = pd.Timestamp(datetime.now(timezone.utc).date())

    for row in profiles_df.itertuples(index=False):
        profile_id = int(getattr(row, "profile_id"))
        years_experience = int(getattr(row, "years_experience"))
        domain = str(getattr(row, "primary_domain"))
        profile_seniority = str(getattr(row, "seniority"))
        profile_skills = from_pipe_list(getattr(row, "skills"))
        profile_sectors = from_pipe_list(getattr(row, "sectors"))
        availability_days = int(getattr(row, "availability_days"))

        n_experiences = int(rng.integers(2, 6))
        total_months = max(years_experience * 12, n_experiences * 8)
        durations = allocate_months(total_months, n_experiences, rng, minimum=6)

        latest_end = today - pd.Timedelta(days=max(0, availability_days))

        spans_rev: list[tuple[pd.Timestamp, pd.Timestamp, int]] = []
        end_cursor = latest_end
        for duration in durations:
            start = end_cursor - pd.DateOffset(months=int(duration))
            spans_rev.append((start, end_cursor, int(duration)))
            end_cursor = start - pd.Timedelta(days=int(rng.integers(10, 45)))

        spans = list(reversed(spans_rev))
        target_rank = SENIORITY_META[profile_seniority]["rank"]

        for idx, (start_date, end_date, duration_months) in enumerate(spans):
            progress = (idx + 1) / max(n_experiences, 1)
            rank = min(target_rank, max(0, int(round(target_rank * progress))))
            seniority = RANK_TO_SENIORITY[rank]

            job_title = f"{str(rng.choice(DOMAIN_TITLES[domain]))} {seniority}"
            client_sector = (
                str(rng.choice(profile_sectors)) if profile_sectors else str(rng.choice(SECTORS))
            )

            skills_count = (
                int(rng.integers(3, min(6, len(profile_skills)) + 1))
                if profile_skills
                else 0
            )
            exp_skills = (
                list(rng.choice(profile_skills, size=skills_count, replace=False))
                if skills_count
                else []
            )

            records.append(
                {
                    "experience_id": experience_id,
                    "profile_id": profile_id,
                    "job_title": job_title,
                    "client_sector": client_sector,
                    "start_date": start_date.date().isoformat(),
                    "end_date": end_date.date().isoformat(),
                    "duration_months": duration_months,
                    "experience_skills": to_pipe_list(sorted(exp_skills)),
                    "experience_summary": (
                        f"Intervention comme {job_title.lower()} pour un client du secteur "
                        f"{client_sector.lower()}, avec delivery sur "
                        f"{', '.join(exp_skills[:4]) if exp_skills else domain}."
                    ),
                }
            )
            experience_id += 1

    return pd.DataFrame(records)


def generate_missions(n_missions: int, rng: np.random.Generator) -> pd.DataFrame:
    records: list[dict[str, Any]] = []

    for mission_id in range(1, n_missions + 1):
        domain = weighted_choice(rng, DOMAINS, DOMAIN_WEIGHTS)
        role = str(rng.choice(MISSION_ROLES[domain]))
        sector = str(rng.choice(SECTORS))

        required_seniority = weighted_choice(
            rng,
            list(SENIORITY_META.keys()),
            np.array([0.08, 0.35, 0.40, 0.17]),
        )
        required_location = weighted_choice(
            rng,
            LOCATIONS,
            np.array([0.22, 0.12, 0.08, 0.10, 0.08, 0.10, 0.07, 0.23]),
        )
        required_language = weighted_choice(rng, LANGUAGES, np.array([0.40, 0.20, 0.40]))

        core_count = int(rng.integers(3, 6))
        core_required = list(rng.choice(DOMAIN_SKILLS[domain], size=core_count, replace=False))
        extra_pool = [skill for skill in ALL_SKILLS if skill not in core_required]
        extra_required = list(rng.choice(extra_pool, size=int(rng.integers(1, 3)), replace=False))
        required_skills = sorted(set(core_required + extra_required))

        desired_start_in_days = int(rng.choice([0, 15, 30, 60], p=[0.20, 0.35, 0.30, 0.15]))
        duration_months = int(rng.integers(3, 19))
        max_daily_rate = mission_budget(required_seniority, domain, rng)

        if desired_start_in_days <= 15:
            priority = weighted_choice(rng, ["High", "Medium", "Low"], np.array([0.65, 0.30, 0.05]))
        else:
            priority = weighted_choice(rng, ["High", "Medium", "Low"], np.array([0.25, 0.55, 0.20]))

        title = f"{role} {required_skills[0]} pour {sector.lower()}"
        description = (
            f"Recherche {role} pour un client {sector.lower()} dans un contexte de transformation "
            f"{domain.lower()}. Competences attendues: {', '.join(required_skills[:6])}. "
            f"Demarrage souhaite dans {desired_start_in_days} jours, duree {duration_months} mois. "
            f"Niveau requis: {required_seniority}. Langue requise: {required_language}. "
            f"Localisation: {required_location}. Budget max: {max_daily_rate} EUR/jour."
        )

        created_at = (
            datetime.now(timezone.utc) - timedelta(days=int(rng.integers(0, 240)))
        ).replace(microsecond=0).isoformat()

        records.append(
            {
                "mission_id": mission_id,
                "title": title,
                "description": description,
                "required_seniority": required_seniority,
                "required_location": required_location,
                "required_languages": required_language,
                "required_skills": to_pipe_list(required_skills),
                "sector": sector,
                "desired_start_in_days": desired_start_in_days,
                "duration_months": duration_months,
                "max_daily_rate": max_daily_rate,
                "priority": priority,
                "created_at": created_at,
            }
        )

    return pd.DataFrame(records)


def build_profile_views(profiles_df: pd.DataFrame) -> list[ProfileView]:
    return [
        ProfileView(
            profile_id=int(row.profile_id),
            full_name=str(row.full_name),
            title=str(row.title),
            seniority=str(row.seniority),
            location=str(row.location),
            language=str(row.languages),
            availability_days=int(row.availability_days),
            years_experience=int(row.years_experience),
            daily_rate=float(row.daily_rate),
            primary_domain=str(row.primary_domain),
            sectors=set(from_pipe_list(row.sectors)),
            skills=set(from_pipe_list(row.skills)),
            cv_text=normalize_text(str(row.cv_text)),
        )
        for row in profiles_df.itertuples(index=False)
    ]


def build_mission_views(missions_df: pd.DataFrame) -> list[MissionView]:
    views: list[MissionView] = []
    for row in missions_df.itertuples(index=False):
        required_skills = set(from_pipe_list(row.required_skills))
        views.append(
            MissionView(
                mission_id=int(row.mission_id),
                title=str(row.title),
                description=normalize_text(str(row.description)),
                required_seniority=str(row.required_seniority),
                required_location=str(row.required_location),
                required_language=str(row.required_languages),
                required_skills=required_skills,
                sector=str(row.sector),
                desired_start_in_days=int(row.desired_start_in_days),
                duration_months=int(row.duration_months),
                max_daily_rate=float(row.max_daily_rate),
                priority=str(row.priority),
                inferred_domain=infer_domain(required_skills),
            )
        )
    return views


def score_language(required: str, candidate: str) -> float:
    if required == "Bilingue":
        return 1.0 if candidate == "Bilingue" else 0.60
    if candidate == "Bilingue":
        return 1.0
    return 1.0 if required == candidate else 0.25


def score_location(required: str, candidate: str) -> float:
    if required == candidate:
        return 1.0
    if required == "Remote" or candidate == "Remote":
        return 0.85
    if required in FRENCH_CITIES and candidate in FRENCH_CITIES:
        return 0.55
    if {required, candidate} == {"Paris", "Bruxelles"}:
        return 0.65
    return 0.15


def score_seniority(required: str, candidate: str) -> float:
    req_rank = SENIORITY_META[required]["rank"]
    cand_rank = SENIORITY_META[candidate]["rank"]
    delta = cand_rank - req_rank
    if delta >= 0:
        return max(0.70, 1.0 - 0.12 * delta)
    if delta == -1:
        return 0.55
    if delta == -2:
        return 0.25
    return 0.05


def score_availability(availability_days: int, desired_start_days: int) -> float:
    if availability_days <= desired_start_days:
        return 1.0
    gap = availability_days - desired_start_days
    if gap <= 15:
        return 0.75
    if gap <= 30:
        return 0.50
    if gap <= 60:
        return 0.30
    return 0.05


def score_rate(rate: float, max_rate: float) -> float:
    if max_rate <= 0:
        return 0.0
    ratio = rate / max_rate
    if ratio <= 0.85:
        return 1.0
    if ratio <= 1.0:
        return 0.85
    if ratio <= 1.10:
        return 0.60
    if ratio <= 1.25:
        return 0.30
    return 0.05


def compute_structured_score(
    mission: MissionView,
    profile: ProfileView,
) -> tuple[float, dict[str, float]]:
    language_score = score_language(mission.required_language, profile.language)
    location_score = score_location(mission.required_location, profile.location)
    seniority_score = score_seniority(mission.required_seniority, profile.seniority)
    availability_score = score_availability(
        profile.availability_days,
        mission.desired_start_in_days,
    )
    rate_score = score_rate(profile.daily_rate, mission.max_daily_rate)

    structured = (
        0.25 * language_score
        + 0.20 * location_score
        + 0.20 * seniority_score
        + 0.20 * availability_score
        + 0.15 * rate_score
    )
    return clamp(structured), {
        "language": language_score,
        "location": location_score,
        "seniority": seniority_score,
        "availability": availability_score,
        "rate": rate_score,
    }


def compute_business_score(
    mission: MissionView,
    profile: ProfileView,
) -> tuple[float, dict[str, float]]:
    sector_bonus = 1.0 if mission.sector in profile.sectors else 0.0
    domain_bonus = 1.0 if mission.inferred_domain == profile.primary_domain else 0.0

    if profile.availability_days <= 15:
        availability_bonus = 1.0
    elif profile.availability_days <= 30:
        availability_bonus = 0.7
    elif profile.availability_days <= 60:
        availability_bonus = 0.4
    else:
        availability_bonus = 0.1

    critical_required = mission.required_skills.intersection(CRITICAL_SKILLS)
    if critical_required:
        critical_overlap = len(critical_required.intersection(profile.skills)) / len(
            critical_required
        )
    else:
        overlap_count = len(mission.required_skills.intersection(profile.skills))
        critical_overlap = overlap_count / max(1, len(mission.required_skills))

    rate_ratio = profile.daily_rate / max(1.0, mission.max_daily_rate)
    rate_malus = clamp((rate_ratio - 0.95) / 0.35)

    business = (
        0.35 * sector_bonus
        + 0.25 * domain_bonus
        + 0.20 * availability_bonus
        + 0.20 * critical_overlap
        - 0.20 * rate_malus
    )
    return clamp(business), {
        "sector": sector_bonus,
        "domain": domain_bonus,
        "availability": availability_bonus,
        "critical_overlap": critical_overlap,
        "rate_malus": rate_malus,
    }


def compute_semantic_similarity(
    missions: list[MissionView],
    profiles: list[ProfileView],
) -> np.ndarray:
    """
    Baseline semantic layer based on TF-IDF + cosine similarity.

    This function is isolated on purpose so it can later be replaced by
    sentence-transformers embeddings with minimal refactoring.
    """

    if not missions or not profiles:
        return np.zeros((len(missions), len(profiles)), dtype=float)

    mission_texts = [
        f"{mission.title} {mission.description} skills {' '.join(sorted(mission.required_skills))}"
        for mission in missions
    ]
    profile_texts = [
        f"{profile.title} {profile.cv_text} skills {' '.join(sorted(profile.skills))}"
        for profile in profiles
    ]

    corpus = mission_texts + profile_texts
    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=15000)
        matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=15000)
        matrix = vectorizer.fit_transform(corpus)

    mission_matrix = matrix[: len(missions)]
    profile_matrix = matrix[len(missions) :]
    return np.clip(cosine_similarity(mission_matrix, profile_matrix), 0.0, 1.0)


def build_explanation_tags(
    mission: MissionView,
    profile: ProfileView,
    structured_parts: dict[str, float],
    business_parts: dict[str, float],
) -> str:
    tags: list[str] = []

    overlap = sorted(mission.required_skills.intersection(profile.skills))
    for skill in overlap[:3]:
        tags.append(f"{skill} match")

    if structured_parts["seniority"] >= 0.75:
        tags.append("Seniority compatible")
    if structured_parts["language"] >= 0.90:
        tags.append("Language compatible")
    if structured_parts["location"] >= 0.75:
        tags.append("Location compatible")
    if profile.availability_days <= 15:
        tags.append("Available in 15 days")
    elif profile.availability_days <= 30:
        tags.append("Available in 30 days")
    if structured_parts["rate"] >= 0.80:
        tags.append("Rate within budget")
    if mission.sector in profile.sectors:
        tags.append(f"Sector {mission.sector.lower()}")
    if business_parts["domain"] >= 1.0:
        tags.append("Domain aligned")

    deduped: list[str] = []
    for tag in tags:
        if tag not in deduped:
            deduped.append(tag)
    return " | ".join(deduped) if deduped else "Baseline fit"


def generate_matches(
    missions: list[MissionView],
    profiles: list[ProfileView],
    semantic_matrix: np.ndarray,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """
    Generate hidden synthetic ground-truth labels for each mission/profile pair.
    """

    records: list[dict[str, Any]] = []
    for mission_idx, mission in enumerate(missions):
        for profile_idx, profile in enumerate(profiles):
            structured, _ = compute_structured_score(mission, profile)
            semantic = float(semantic_matrix[mission_idx, profile_idx])
            business, _ = compute_business_score(mission, profile)

            structured_true = clamp(structured + float(rng.normal(0, 0.03)))
            semantic_true = clamp(semantic + float(rng.normal(0, 0.03)))
            business_true = clamp(business + float(rng.normal(0, 0.04)))
            final_true = clamp(0.40 * structured_true + 0.40 * semantic_true + 0.20 * business_true)

            records.append(
                {
                    "mission_id": mission.mission_id,
                    "profile_id": profile.profile_id,
                    "structured_score_true": round(structured_true, 4),
                    "semantic_score_true": round(semantic_true, 4),
                    "business_score_true": round(business_true, 4),
                    "final_score_true": round(final_true, 4),
                    "label": 0,
                }
            )

    matches_df = pd.DataFrame(records)

    # Assign labels mission by mission from ranking to keep realistic imbalance.
    for _mission_id, index_values in matches_df.groupby("mission_id").groups.items():
        ordered = matches_df.loc[list(index_values)].sort_values(
            "final_score_true",
            ascending=False,
        )
        total = len(ordered)

        high_count = max(5, int(round(0.02 * total)))
        medium_count = max(20, int(round(0.10 * total)))

        high_indexes = ordered.index[:high_count]
        medium_indexes = ordered.index[high_count : high_count + medium_count]

        matches_df.loc[high_indexes, "label"] = 2
        matches_df.loc[medium_indexes, "label"] = 1

    return matches_df[
        [
            "mission_id",
            "profile_id",
            "structured_score_true",
            "semantic_score_true",
            "business_score_true",
            "final_score_true",
            "label",
        ]
    ]


def build_recommendations(
    missions: list[MissionView],
    profiles: list[ProfileView],
    semantic_matrix: np.ndarray,
    top_k: int,
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for mission_idx, mission in enumerate(missions):
        mission_records: list[dict[str, Any]] = []
        for profile_idx, profile in enumerate(profiles):
            structured, structured_parts = compute_structured_score(mission, profile)
            semantic = float(semantic_matrix[mission_idx, profile_idx])
            business, business_parts = compute_business_score(mission, profile)
            final_score = clamp(0.40 * structured + 0.40 * semantic + 0.20 * business)

            mission_records.append(
                {
                    "mission_id": mission.mission_id,
                    "profile_id": profile.profile_id,
                    "structured_score": round(structured, 4),
                    "semantic_score": round(semantic, 4),
                    "business_score": round(business, 4),
                    "final_score": round(final_score, 4),
                    "explanation_tags": build_explanation_tags(
                        mission,
                        profile,
                        structured_parts,
                        business_parts,
                    ),
                }
            )

        mission_records.sort(key=lambda row: row["final_score"], reverse=True)
        records.extend(mission_records[: max(1, top_k)])

    return pd.DataFrame(
        records,
        columns=[
            "mission_id",
            "profile_id",
            "structured_score",
            "semantic_score",
            "business_score",
            "final_score",
            "explanation_tags",
        ],
    )


def print_summary_stats(
    profiles_df: pd.DataFrame,
    experiences_df: pd.DataFrame,
    missions_df: pd.DataFrame,
    matches_df: pd.DataFrame,
) -> None:
    experiences_per_profile = experiences_df.groupby("profile_id").size()
    avg_experiences = (
        float(experiences_per_profile.mean()) if not experiences_per_profile.empty else 0.0
    )

    print("\n=== Summary Statistics ===")
    print(f"Number of profiles: {len(profiles_df)}")
    print(f"Number of missions: {len(missions_df)}")
    print(f"Average number of experiences: {avg_experiences:.2f}")

    print("\nDistribution of seniority:")
    print(profiles_df["seniority"].value_counts().to_string())

    print("\nDistribution of labels in matches.csv:")
    counts = matches_df["label"].value_counts().sort_index()
    perc = (matches_df["label"].value_counts(normalize=True).sort_index() * 100).round(2)
    for label in [0, 1, 2]:
        print(f"Label {label}: {counts.get(label, 0)} ({perc.get(label, 0.0)}%)")


def print_example_recommendations(
    recommendations_df: pd.DataFrame,
    missions_df: pd.DataFrame,
    profiles_df: pd.DataFrame,
    rng: np.random.Generator,
    examples: int = 3,
) -> None:
    if recommendations_df.empty:
        print("\nNo recommendations to display.")
        return

    mission_ids = recommendations_df["mission_id"].unique().tolist()
    if not mission_ids:
        print("\nNo mission ids found in recommendations.")
        return

    mission_title_by_id = dict(zip(missions_df["mission_id"], missions_df["title"]))
    profile_name_by_id = dict(zip(profiles_df["profile_id"], profiles_df["full_name"]))

    picked = rng.choice(mission_ids, size=min(examples, len(mission_ids)), replace=False)
    print("\n=== Mission -> Top Profiles Examples ===")
    for mission_id in picked:
        print(f"\nMission {mission_id}: {mission_title_by_id.get(mission_id, 'Unknown mission')}")
        top_rows = (
            recommendations_df[recommendations_df["mission_id"] == mission_id]
            .sort_values("final_score", ascending=False)
            .head(5)
        )
        for rank, row in enumerate(top_rows.itertuples(index=False), start=1):
            profile_id = int(row.profile_id)
            profile_name = profile_name_by_id.get(profile_id, f"Profile {profile_id}")
            print(
                f"  {rank}. {profile_name} (id={profile_id}) "
                f"score={row.final_score:.3f} | {row.explanation_tags}"
            )


def save_outputs(
    output_dir: Path,
    profiles_df: pd.DataFrame,
    experiences_df: pd.DataFrame,
    missions_df: pd.DataFrame,
    matches_df: pd.DataFrame,
    recommendations_df: pd.DataFrame,
) -> None:
    profiles_df.to_csv(output_dir / "profiles.csv", index=False)
    experiences_df.to_csv(output_dir / "experiences.csv", index=False)
    missions_df.to_csv(output_dir / "missions.csv", index=False)
    matches_df.to_csv(output_dir / "matches.csv", index=False)
    recommendations_df.to_csv(output_dir / "recommendations_sample.csv", index=False)


def to_date(value: Any) -> date | None:
    if pd.isna(value):
        return None
    try:
        return pd.to_datetime(value).date()
    except (TypeError, ValueError):
        return None


def load_dataset_to_db(
    profiles_df: pd.DataFrame,
    experiences_df: pd.DataFrame,
    missions_df: pd.DataFrame,
    recommendations_df: pd.DataFrame,
    reset_db: bool = False,
) -> dict[str, int]:
    from app.core.database import SessionLocal
    from app.models.experience import Experience
    from app.models.match_result import MatchResult
    from app.models.mission import Mission
    from app.models.profile import Profile

    inserted_profiles = 0
    inserted_experiences = 0
    inserted_missions = 0
    inserted_matches = 0

    profile_id_map: dict[int, int] = {}
    mission_id_map: dict[int, int] = {}

    db = SessionLocal()
    try:
        if reset_db:
            db.query(MatchResult).delete()
            db.query(Experience).delete()
            db.query(Mission).delete()
            db.query(Profile).delete()
            db.commit()

        for row in profiles_df.sort_values("profile_id").itertuples(index=False):
            profile = Profile(
                full_name=str(getattr(row, "full_name")),
                raw_text=str(getattr(row, "cv_text")),
                parsed_skills=from_pipe_list(getattr(row, "skills")),
                parsed_languages=from_pipe_list(getattr(row, "languages")),
                parsed_location=str(getattr(row, "location")),
                parsed_seniority=str(getattr(row, "seniority")),
                availability_status=str(getattr(row, "availability_status")),
                source="synthetic",
            )
            db.add(profile)
            db.flush()
            profile_id_map[int(getattr(row, "profile_id"))] = int(profile.id)
            inserted_profiles += 1

        for row in experiences_df.sort_values("experience_id").itertuples(index=False):
            synthetic_profile_id = int(getattr(row, "profile_id"))
            db_profile_id = profile_id_map.get(synthetic_profile_id)
            if db_profile_id is None:
                continue

            experience = Experience(
                profile_id=db_profile_id,
                title=str(getattr(row, "job_title")),
                company=str(getattr(row, "client_sector")),
                start_date=to_date(getattr(row, "start_date")),
                end_date=to_date(getattr(row, "end_date")),
                description=str(getattr(row, "experience_summary")),
            )
            db.add(experience)
            inserted_experiences += 1

        for row in missions_df.sort_values("mission_id").itertuples(index=False):
            start_in_days = int(getattr(row, "desired_start_in_days"))
            mission = Mission(
                title=str(getattr(row, "title")),
                description=str(getattr(row, "description")),
                required_skills=from_pipe_list(getattr(row, "required_skills")),
                required_language=str(getattr(row, "required_languages")),
                required_location=str(getattr(row, "required_location")),
                required_seniority=str(getattr(row, "required_seniority")),
                desired_start_date=date.today() + timedelta(days=max(0, start_in_days)),
            )
            db.add(mission)
            db.flush()
            mission_id_map[int(getattr(row, "mission_id"))] = int(mission.id)
            inserted_missions += 1

        for row in recommendations_df.itertuples(index=False):
            synthetic_mission_id = int(getattr(row, "mission_id"))
            synthetic_profile_id = int(getattr(row, "profile_id"))

            db_mission_id = mission_id_map.get(synthetic_mission_id)
            db_profile_id = profile_id_map.get(synthetic_profile_id)
            if db_mission_id is None or db_profile_id is None:
                continue

            match = MatchResult(
                mission_id=db_mission_id,
                profile_id=db_profile_id,
                structured_score=float(getattr(row, "structured_score")),
                semantic_score=float(getattr(row, "semantic_score")),
                business_score=float(getattr(row, "business_score")),
                final_score=float(getattr(row, "final_score")),
                explanation_tags=from_pipe_list(getattr(row, "explanation_tags")),
            )
            db.add(match)
            inserted_matches += 1

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return {
        "profiles": inserted_profiles,
        "experiences": inserted_experiences,
        "missions": inserted_missions,
        "matches": inserted_matches,
    }


def parse_args() -> argparse.Namespace:
    repo_data_default = Path(__file__).resolve().parents[3] / "data"
    parser = argparse.ArgumentParser(
        description="Generate synthetic staffing dataset and a baseline recommendation pipeline."
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument(
        "--profiles",
        type=int,
        default=None,
        help="Number of profiles (300-500 by default).",
    )
    parser.add_argument(
        "--missions",
        type=int,
        default=None,
        help="Number of missions (50-100 by default).",
    )
    parser.add_argument("--top-k", type=int, default=10, help="Top-k recommendations per mission.")
    parser.add_argument(
        "--load-db",
        action="store_true",
        help="Load generated synthetic data into the configured database.",
    )
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help=(
            "Reset profiles/missions/experiences/matches before loading data "
            "(requires --load-db)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_data_default,
        help=f"Output directory for CSV files (default: {repo_data_default}).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.reset_db and not args.load_db:
        raise ValueError("--reset-db requires --load-db.")

    config = GenerationConfig(seed=args.seed, top_k=args.top_k)
    set_seed(config.seed)
    rng = np.random.default_rng(config.seed)
    fake = Faker("fr_FR")
    fake.seed_instance(config.seed)

    n_profiles = args.profiles if args.profiles is not None else int(
        rng.integers(config.min_profiles, config.max_profiles + 1)
    )
    n_missions = args.missions if args.missions is not None else int(
        rng.integers(config.min_missions, config.max_missions + 1)
    )

    if n_profiles < 1 or n_missions < 1:
        raise ValueError("profiles and missions counts must be positive.")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating synthetic MVP dataset...")
    print(f"Profiles target: {n_profiles}")
    print(f"Missions target: {n_missions}")

    profiles_df = generate_profiles(n_profiles=n_profiles, rng=rng, fake=fake)
    experiences_df = generate_experiences(profiles_df=profiles_df, rng=rng)
    missions_df = generate_missions(n_missions=n_missions, rng=rng)

    profile_views = build_profile_views(profiles_df)
    mission_views = build_mission_views(missions_df)

    semantic_matrix = compute_semantic_similarity(mission_views, profile_views)
    matches_df = generate_matches(mission_views, profile_views, semantic_matrix, rng)

    # Load/save contract for baseline pipeline: use generated datasets as source.
    profiles_df.to_csv(output_dir / "profiles.csv", index=False)
    experiences_df.to_csv(output_dir / "experiences.csv", index=False)
    missions_df.to_csv(output_dir / "missions.csv", index=False)

    loaded_profiles = pd.read_csv(output_dir / "profiles.csv")
    loaded_missions = pd.read_csv(output_dir / "missions.csv")

    recommendations_df = build_recommendations(
        missions=build_mission_views(loaded_missions),
        profiles=build_profile_views(loaded_profiles),
        semantic_matrix=compute_semantic_similarity(
            build_mission_views(loaded_missions),
            build_profile_views(loaded_profiles),
        ),
        top_k=config.top_k,
    )

    save_outputs(
        output_dir=output_dir,
        profiles_df=profiles_df,
        experiences_df=experiences_df,
        missions_df=missions_df,
        matches_df=matches_df,
        recommendations_df=recommendations_df,
    )

    if args.load_db:
        print("\nLoading generated synthetic data into database...")
        db_counts = load_dataset_to_db(
            profiles_df=profiles_df,
            experiences_df=experiences_df,
            missions_df=missions_df,
            recommendations_df=recommendations_df,
            reset_db=args.reset_db,
        )
        print("Database load completed:")
        print(f"Profiles inserted: {db_counts['profiles']}")
        print(f"Experiences inserted: {db_counts['experiences']}")
        print(f"Missions inserted: {db_counts['missions']}")
        print(f"Match results inserted: {db_counts['matches']}")

    print_summary_stats(profiles_df, experiences_df, missions_df, matches_df)
    print_example_recommendations(recommendations_df, missions_df, profiles_df, rng, examples=3)

    print("\nGenerated files:")
    print(output_dir / "profiles.csv")
    print(output_dir / "experiences.csv")
    print(output_dir / "missions.csv")
    print(output_dir / "matches.csv")
    print(output_dir / "recommendations_sample.csv")


if __name__ == "__main__":
    main()
