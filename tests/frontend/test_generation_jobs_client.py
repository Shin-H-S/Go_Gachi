import pytest

from frontend.services import generation_jobs_client


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


def test_generate_job_polling_waits_one_second_between_status_checks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleep_calls: list[int] = []

    def fake_post(
        url: str,  # noqa: ARG001
        json: dict[str, object],  # noqa: ARG001
        headers: dict[str, str],  # noqa: ARG001
        timeout: int,  # noqa: ARG001
    ) -> FakeResponse:
        return FakeResponse({"requestId": "job-1"})

    def fake_get(
        url: str,  # noqa: ARG001
        headers: dict[str, str],  # noqa: ARG001
        timeout: int,  # noqa: ARG001
    ) -> FakeResponse:
        return FakeResponse(
            {
                "status": "success",
                "imageUrl": "/outputs/job-result.png",
            }
        )

    monkeypatch.setattr(generation_jobs_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(generation_jobs_client.httpx, "post", fake_post)
    monkeypatch.setattr(generation_jobs_client.httpx, "get", fake_get)
    monkeypatch.setattr(generation_jobs_client.time, "sleep", sleep_calls.append)

    result = generation_jobs_client.request_generate_job_result({"prompt": "coffee"}, "jwt-token")

    assert sleep_calls == [1]
    assert str(result["imageUrl"]).endswith("/outputs/job-result.png")
