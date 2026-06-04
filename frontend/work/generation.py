import time

import httpx
import streamlit as st

from frontend.media.mock_banner import create_mock_banner
from frontend.services.api_client import (
    BACKEND_URL,
    FRONTEND_USE_MOCK,
    build_feedback,
    request_backend,
)


def handle_generation_request(
    *,
    generate,
    uploaded_file,
    prompt: str,
    format_label: str,
    detail_label: str,
    current_result_context,
) -> None:
    if generate:
        if not uploaded_file:
            st.warning("메뉴 사진을 먼저 업로드해주세요.")
        elif not prompt.strip():
            st.warning("프롬프트를 입력해주세요.")
        else:
            try:
                time.sleep(1.2)
                if FRONTEND_USE_MOCK:
                    result_bytes = create_mock_banner(
                        image_bytes=uploaded_file.getvalue(),
                        prompt=build_feedback(prompt.strip(), detail_label),
                        format_label=format_label,
                        detail_label=detail_label,
                    )
                else:
                    result_bytes = request_backend(
                        uploaded_file,
                        prompt.strip(),
                        format_label,
                        detail_label,
                    )
                st.session_state["result_bytes"] = result_bytes
                st.session_state["result_context"] = current_result_context
                st.rerun()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text
                st.error(f"백엔드 생성 요청 실패 [HTTP {exc.response.status_code}]: {detail}")
            except httpx.HTTPError as exc:
                st.error(
                    f"백엔드 연결 실패 [NETWORK_ERROR] {BACKEND_URL}: "
                    f"{type(exc).__name__}: {exc}"
                )
            except Exception as exc:
                st.error(f"이미지 생성 중 오류가 발생했습니다: {exc}")
