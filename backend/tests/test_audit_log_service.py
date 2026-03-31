from app.services.audit_log_service import append_audit_event, read_audit_events


def test_append_and_read_audit_events():
    append_audit_event(
        "custom_event",
        {
            "scope": "test",
            "ok": True,
            "details": {"k": "v"},
        },
    )

    events = read_audit_events(limit=10)
    assert len(events) >= 1

    last = events[-1]
    assert last["event_type"] == "custom_event"
    assert last["scope"] == "test"
    assert last["ok"] is True
    assert last["details"] == {"k": "v"}
