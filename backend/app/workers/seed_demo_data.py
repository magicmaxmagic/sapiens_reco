from __future__ import annotations

import argparse
import random
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.experience import Experience
from app.models.match_result import MatchResult
from app.models.mission import Mission
from app.models.profile import Profile
from app.services.matching_service import score_profile_for_mission

FIRST_NAMES = [
    "Camille",
    "Mathieu",
    "Sofia",
    "Romain",
    "Lea",
    "Nora",
    "Yanis",
    "Ines",
    "Thomas",
    "Julie",
    "Alex",
    "Nicolas",
]

LAST_NAMES = [
    "Martin",
    "Bernard",
    "Dubois",
    "Thomas",
    "Robert",
    "Richard",
    "Petit",
    "Durand",
    "Leroy",
    "Moreau",
    "Simon",
    "Laurent",
]

SKILLS = [
    "python",
    "fastapi",
    "sql",
    "postgresql",
    "docker",
    "kubernetes",
    "react",
    "next.js",
    "typescript",
    "aws",
    "azure",
    "pandas",
    "numpy",
    "scikit-learn",
]

LANGUAGES = ["fr", "en", "es", "de"]
LOCATIONS = ["paris", "lyon", "lille", "toulouse", "nantes", "remote", "hybride"]
SENIORITIES = ["junior", "mid", "senior", "lead"]
AVAILABILITIES = ["available", "soon", "unknown", "open"]

MISSION_TITLES = [
    "Data Engineer",
    "ML Engineer",
    "Backend Python",
    "Tech Lead Data",
    "Fullstack Staffing Platform",
    "Data Analyst Senior",
    "Platform Engineer",
    "AI Product Engineer",
]


def _build_profile(index: int, rng: random.Random) -> Profile:
    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)
    full_name = f"{first} {last} {index:03d}"

    seniority = rng.choice(SENIORITIES)
    years = {
        "junior": rng.randint(1, 2),
        "mid": rng.randint(3, 5),
        "senior": rng.randint(6, 9),
        "lead": rng.randint(10, 14),
    }[seniority]

    skills = sorted(rng.sample(SKILLS, k=rng.randint(4, 7)))
    languages = sorted(rng.sample(LANGUAGES, k=rng.randint(1, 3)))
    location = rng.choice(LOCATIONS)

    raw_text = (
        f"{full_name} with {years} years experience in {location}. "
        f"Core skills: {', '.join(skills)}. Languages: {', '.join(languages)}. "
        "Delivered data and staffing projects for enterprise clients."
    )

    profile = Profile(
        full_name=full_name,
        raw_text=raw_text,
        parsed_skills=skills,
        parsed_languages=languages,
        parsed_location=location,
        parsed_seniority=seniority,
        availability_status=rng.choice(AVAILABILITIES),
        source="seed",
    )

    profile.experiences = [
        Experience(
            title=rng.choice(["Data Engineer", "Backend Engineer", "ML Engineer", "Tech Lead"]),
            company=rng.choice(["Acme", "Globex", "Innotech", "Sapiens", "Octo"]),
            start_date=date.today() - timedelta(days=(years + 2) * 365),
            end_date=date.today() - timedelta(days=365),
            description="Built production systems and improved staffing efficiency.",
        )
    ]

    return profile


def _build_mission(index: int, rng: random.Random) -> Mission:
    title = f"{rng.choice(MISSION_TITLES)} #{index:02d}"
    required_skills = sorted(rng.sample(SKILLS, k=rng.randint(3, 5)))
    required_language = rng.choice(["fr", "en", None])
    required_location = rng.choice(LOCATIONS)
    required_seniority = rng.choice(SENIORITIES)

    description = (
        f"Need {required_seniority} profile with {', '.join(required_skills)}. "
        f"Location {required_location}, language {required_language or 'any'}."
    )

    return Mission(
        title=title,
        description=description,
        required_skills=required_skills,
        required_language=required_language,
        required_location=required_location,
        required_seniority=required_seniority,
        desired_start_date=date.today() + timedelta(days=rng.randint(7, 60)),
    )


def _reset_demo_data(db: Session) -> None:
    db.query(MatchResult).delete()
    db.query(Experience).delete()
    db.query(Mission).delete()
    db.query(Profile).delete()
    db.commit()


def _seed_profiles(db: Session, profiles_count: int, rng: random.Random) -> list[Profile]:
    profiles = [_build_profile(index=i + 1, rng=rng) for i in range(profiles_count)]
    db.add_all(profiles)
    db.commit()

    for profile in profiles:
        db.refresh(profile)

    return profiles


def _seed_missions(db: Session, missions_count: int, rng: random.Random) -> list[Mission]:
    missions = [_build_mission(index=i + 1, rng=rng) for i in range(missions_count)]
    db.add_all(missions)
    db.commit()

    for mission in missions:
        db.refresh(mission)

    return missions


def _seed_matches(db: Session, missions: list[Mission], profiles: list[Profile]) -> int:
    inserted = 0
    for mission in missions:
        for profile in profiles:
            score = score_profile_for_mission(mission, profile)
            if float(score["final_score"]) < 35:
                continue
            db.add(
                MatchResult(
                    mission_id=mission.id,
                    profile_id=profile.id,
                    structured_score=float(score["structured_score"]),
                    semantic_score=float(score["semantic_score"]),
                    business_score=float(score["business_score"]),
                    final_score=float(score["final_score"]),
                    explanation_tags=list(score["explanation_tags"]),
                )
            )
            inserted += 1

    db.commit()
    return inserted


def run_seed(
    profiles_count: int,
    missions_count: int,
    reset: bool,
    with_matches: bool,
    seed: int,
) -> None:
    rng = random.Random(seed)

    db = SessionLocal()
    try:
        if reset:
            _reset_demo_data(db)

        profiles = _seed_profiles(db, profiles_count=profiles_count, rng=rng)
        missions = _seed_missions(db, missions_count=missions_count, rng=rng)

        match_count = 0
        if with_matches:
            match_count = _seed_matches(db, missions=missions, profiles=profiles)

        print(
            "Seed complete:",
            f"profiles={len(profiles)}",
            f"missions={len(missions)}",
            f"matches={match_count}",
        )
    finally:
        db.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed demo data for Optimus MVP")
    parser.add_argument(
        "--profiles",
        type=int,
        default=120,
        help="Number of synthetic profiles",
    )
    parser.add_argument("--missions", type=int, default=8, help="Number of synthetic missions")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing profiles/missions/matches",
    )
    parser.add_argument(
        "--with-matches",
        action="store_true",
        help="Compute and persist initial match results",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic generation",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.profiles < 50 or args.profiles > 200:
        raise SystemExit("--profiles must be between 50 and 200 for demo scenarios")

    if args.missions < 1 or args.missions > 50:
        raise SystemExit("--missions must be between 1 and 50")

    run_seed(
        profiles_count=args.profiles,
        missions_count=args.missions,
        reset=args.reset,
        with_matches=args.with_matches,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
