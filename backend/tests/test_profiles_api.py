def test_manual_profile_correction_endpoint(client, admin_headers):
    upload = client.post(
        "/api/profiles/upload",
        files={"file": ("john_doe.txt", b"John Doe Python english Paris 5 years", "text/plain")},
        headers=admin_headers,
    )

    assert upload.status_code == 200
    profile_id = upload.json()["id"]

    correction = client.post(
        f"/api/profiles/{profile_id}/manual-correction",
        json={
            "full_name": "John Doe Updated",
            "parsed_skills": ["python", "fastapi"],
            "parsed_languages": ["en", "fr"],
            "parsed_location": "lyon",
            "parsed_seniority": "senior",
            "availability_status": "available",
        },
        headers=admin_headers,
    )

    assert correction.status_code == 200
    body = correction.json()
    assert body["full_name"] == "John Doe Updated"
    assert body["parsed_location"] == "lyon"
    assert body["availability_status"] == "available"
    assert body["parsed_skills"] == ["python", "fastapi"]


def test_upload_rejects_unsupported_extension(client, admin_headers):
    response = client.post(
        "/api/profiles/upload",
        files={"file": ("malicious.exe", b"bad", "application/octet-stream")},
        headers=admin_headers,
    )

    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]
