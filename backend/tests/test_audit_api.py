def test_audit_export_json_and_jsonl(client, admin_headers):
    health = client.get("/api/health")
    assert health.status_code == 200

    response_json = client.get(
        "/api/audit/logs/export?format=json&limit=50",
        headers=admin_headers,
    )
    assert response_json.status_code == 200
    body = response_json.json()
    assert body["count"] >= 1
    assert any(event.get("event_type") == "http_request" for event in body["items"])

    response_jsonl = client.get(
        "/api/audit/logs/export?format=jsonl&limit=50",
        headers=admin_headers,
    )
    assert response_jsonl.status_code == 200
    assert response_jsonl.text.strip() != ""
