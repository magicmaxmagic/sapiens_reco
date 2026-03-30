from app.models.mission import Mission
from app.models.profile import Profile
from app.services.matching_service import score_profile_for_mission
from app.services.parsing_service import parse_profile_document


def test_parse_profile_document_from_text_file():
    content = b"John Doe Python FastAPI 5 years Paris English Francais"
    parsed = parse_profile_document("john_doe.txt", content)

    assert parsed["full_name"] == "John Doe"
    assert "python" in parsed["parsed_skills"]
    assert parsed["parsed_seniority"] in {"mid", "senior", "lead"}


def test_score_profile_for_mission():
    mission = Mission(
        title="Data Engineer Python",
        description="Need Python and SQL for staffing project",
        required_skills=["python", "sql"],
        required_language="en",
        required_location="paris",
        required_seniority="mid",
    )
    profile = Profile(
        full_name="Jane Doe",
        raw_text="Python SQL FastAPI engineer with 6 years experience in Paris",
        parsed_skills=["python", "sql", "fastapi"],
        parsed_languages=["en", "fr"],
        parsed_location="paris",
        parsed_seniority="senior",
        availability_status="available",
        source="upload",
    )

    result = score_profile_for_mission(mission, profile)

    assert result["final_score"] >= 60
    assert "language_match" in result["explanation_tags"]
