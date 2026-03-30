def test_e2e_admin_upload_mission_match_and_audit_export(client, admin_headers):
    upload = client.post(
        "/api/profiles/upload",
        files={
            "file": (
                "alice_engineer.txt",
                b"Alice Python FastAPI SQL Paris English 6 years available",
                "text/plain",
            )
        },
        headers=admin_headers,
    )
    assert upload.status_code == 200

    mission = client.post(
        "/api/missions",
        json={
            "title": "Senior Backend Python",
            "description": "Need Python FastAPI SQL profile in Paris",
            "required_skills": ["python", "fastapi", "sql"],
            "required_language": "en",
            "required_location": "paris",
            "required_seniority": "mid",
            "desired_start_date": None,
        },
        headers=admin_headers,
    )
    assert mission.status_code == 200
    mission_id = mission.json()["id"]

    matching = client.post(f"/api/missions/{mission_id}/match?top_n=10", headers=admin_headers)
    assert matching.status_code == 200
    matches = matching.json()
    assert isinstance(matches, list)
    assert len(matches) >= 1

    export_json = client.get("/api/audit/logs/export?format=json&limit=50", headers=admin_headers)
    assert export_json.status_code == 200
    assert export_json.json()["count"] >= 1

    export_jsonl = client.get("/api/audit/logs/export?format=jsonl&limit=50", headers=admin_headers)
    assert export_jsonl.status_code == 200
    assert export_jsonl.text.strip() != ""
