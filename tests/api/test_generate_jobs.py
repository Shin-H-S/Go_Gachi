from backend.app.core.auth import AuthUser, get_current_user
from backend.app.main import app
from backend.app.services import generation_service
from backend.app.services.generation_jobs import _jobs
from tests.api.helpers import TINY_PNG_B64, TINY_PNG_DATA_URL, client, force_openai_mode


def _user(user_id: str) -> AuthUser:
    return AuthUser(
        id=user_id,
        email=f"{user_id}@example.com",
        role="user",
        display_name="User",
    )


def test_generate_job_completes_and_status_returns_urls(monkeypatch) -> None:
    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        return TINY_PNG_B64, {}

    async def _override_user() -> AuthUser:
        return _user("job-user")

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)
    app.dependency_overrides[get_current_user] = _override_user
    try:
        create_response = client.post(
            "/api/generate/jobs",
            json={
                "imageDataUrl": TINY_PNG_DATA_URL,
                "presetId": "instagram",
                "userPrompt": "job unique prompt one",
            },
        )
        request_id = create_response.json()["requestId"]
        status_response = client.get(f"/api/generate/jobs/{request_id}")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert create_response.status_code == 200
    assert create_response.json() == {
        "requestId": request_id,
        "jobId": request_id,
        "status": "pending",
    }
    assert status_response.status_code == 200
    body = status_response.json()
    assert body["requestId"] == request_id
    assert body["jobId"] == request_id
    assert body["status"] == "success"
    assert body["imageUrl"] == f"/outputs/{request_id}.png"
    assert body["originalImageUrl"] == f"/uploads/{request_id}.png"
    assert body["error"] is None


def test_generate_job_status_is_user_scoped(monkeypatch) -> None:
    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        return TINY_PNG_B64, {}

    async def _owner() -> AuthUser:
        return _user("job-owner")

    async def _other() -> AuthUser:
        return _user("job-other")

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)
    app.dependency_overrides[get_current_user] = _owner
    try:
        create_response = client.post(
            "/api/generate/jobs",
            json={
                "imageDataUrl": TINY_PNG_DATA_URL,
                "presetId": "instagram",
                "userPrompt": "job unique prompt scoped",
            },
        )
        request_id = create_response.json()["requestId"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    app.dependency_overrides[get_current_user] = _other
    try:
        status_response = client.get(f"/api/generate/jobs/{request_id}")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert status_response.status_code == 404


def test_generate_job_failure_hides_raw_exception(monkeypatch) -> None:
    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        raise RuntimeError("secret internal failure")

    async def _override_user() -> AuthUser:
        return _user("job-error-user")

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)
    app.dependency_overrides[get_current_user] = _override_user
    try:
        create_response = client.post(
            "/api/generate/jobs",
            json={
                "imageDataUrl": TINY_PNG_DATA_URL,
                "presetId": "instagram",
                "userPrompt": "job unique prompt failure",
            },
        )
        request_id = create_response.json()["requestId"]
        status_response = client.get(f"/api/generate/jobs/{request_id}")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "failed"
    assert status_response.json()["error"] != "secret internal failure"


def test_done_memory_job_is_cleaned_after_20_minutes(monkeypatch) -> None:
    from datetime import UTC, datetime, timedelta

    from backend.app.services import generation_jobs
    from backend.app.services.generation_jobs import TransientJob

    old_time = datetime.now(UTC) - timedelta(minutes=21)
    _jobs["old-done-job"] = TransientJob(
        user_id="job-cleanup-user",
        status="done",
        error=None,
        created_at=old_time,
        updated_at=old_time,
    )

    async def _override_user() -> AuthUser:
        return _user("job-cleanup-user")

    async def _fake_status(*args: object, **kwargs: object) -> None:
        return None

    monkeypatch.setattr(generation_jobs.crud, "get_user_generation_by_request_id", _fake_status)
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.get("/api/generate/jobs/old-done-job")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 404
    assert "old-done-job" not in _jobs
