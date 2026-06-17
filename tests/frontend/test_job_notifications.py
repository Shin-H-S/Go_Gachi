from frontend.work import job_notifications


class FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.toasts: list[str] = []

    def toast(self, message: str) -> None:
        self.toasts.append(message)


def test_completed_generation_job_appends_result_and_toasts(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state["auth_access_token"] = "jwt-token"
    fake_st.session_state["active_generation_jobs"] = {
        "job-1": {
            "requestId": "job-1",
            "status": "pending",
            "context": {"uploadHash": "hash-1", "prompt": "따뜻하게"},
            "format_label": "인스타그램",
            "detail_label": "정사각형 피드",
        }
    }

    def fake_status(request_id: str, access_token: str) -> dict[str, object]:
        assert request_id == "job-1"
        assert access_token == "jwt-token"
        return {
            "status": "success",
            "imageUrl": "https://assets.example/result.png",
            "copy": {"headline": "오늘의 라떼"},
        }

    monkeypatch.setattr(job_notifications, "st", fake_st)
    monkeypatch.setattr(job_notifications, "get_generation_job_status", fake_status)

    job_notifications.process_generation_job_notifications()

    assert fake_st.session_state["active_generation_jobs"] == {}
    assert fake_st.session_state["result_image_url"] == "https://assets.example/result.png"
    assert fake_st.session_state["result_copy"] == {"headline": "오늘의 라떼"}
    assert fake_st.toasts == ["이미지 생성이 완료됐어요."]


def test_done_generation_job_with_image_url_finishes_loading(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state["auth_access_token"] = "jwt-token"
    fake_st.session_state["active_generation_jobs"] = {
        "job-1": {
            "requestId": "job-1",
            "status": "processing",
            "context": {"uploadHash": "hash-1"},
            "format_label": "인스타그램",
            "detail_label": "정사각형 피드",
        }
    }

    monkeypatch.setattr(job_notifications, "st", fake_st)
    monkeypatch.setattr(
        job_notifications,
        "get_generation_job_status",
        lambda request_id, access_token: {
            "status": "done",
            "imageUrl": "https://assets.example/done.png",
        },
    )

    job_notifications.process_generation_job_notifications()

    assert not job_notifications.has_active_generation_job(fake_st.session_state)
    assert fake_st.session_state["result_image_url"] == "https://assets.example/done.png"
    assert fake_st.toasts == ["이미지 생성이 완료됐어요."]


def test_queued_generation_toast_renders_after_rerun(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state["generation_toasts"] = ["이미지 생성을 시작했어요."]
    monkeypatch.setattr(job_notifications, "st", fake_st)

    job_notifications.render_queued_generation_toasts()

    assert fake_st.toasts == ["이미지 생성을 시작했어요."]
    assert "generation_toasts" not in fake_st.session_state


def test_waiting_generation_job_stays_active(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state["auth_access_token"] = "jwt-token"
    fake_st.session_state["active_generation_jobs"] = {
        "job-1": {"requestId": "job-1", "status": "pending"}
    }

    monkeypatch.setattr(job_notifications, "st", fake_st)
    monkeypatch.setattr(
        job_notifications,
        "get_generation_job_status",
        lambda request_id, access_token: {"status": "processing"},
    )

    job_notifications.process_generation_job_notifications()

    assert job_notifications.has_active_generation_job(fake_st.session_state)
    assert fake_st.session_state["active_generation_jobs"]["job-1"]["status"] == "processing"
    assert fake_st.toasts == []


def test_failed_generation_job_is_removed_with_toast(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state["auth_access_token"] = "jwt-token"
    fake_st.session_state["active_generation_jobs"] = {
        "job-1": {"requestId": "job-1", "status": "pending"}
    }

    monkeypatch.setattr(job_notifications, "st", fake_st)
    monkeypatch.setattr(
        job_notifications,
        "get_generation_job_status",
        lambda request_id, access_token: {"status": "failed", "error": "IMAGE_API_TIMEOUT"},
    )

    job_notifications.process_generation_job_notifications()

    assert fake_st.session_state["active_generation_jobs"] == {}
    assert fake_st.toasts == ["이미지 생성에 실패했어요: IMAGE_API_TIMEOUT"]
