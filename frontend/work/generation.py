import time

import httpx
import streamlit as st

from frontend.media.mock_banner import create_mock_banner
from frontend.services.api_client import (
    BACKEND_URL,
    FRONTEND_USE_MOCK,
    GenerationResult,
    request_backend,
)


def _mock_copy_info(text: str, copy_mode: str) -> dict[str, object]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    headline = lines[0] if lines else text
    subcopy = "\n".join(lines[1:]) or None
    return {"headline": headline, "subcopy": subcopy, "cta": None, "copyMode": copy_mode}


def handle_generation_request(
    *,
    generate,
    uploaded_file,
    logo_file,
    prompt: str,
    ad_copy_prompt: str,
    format_label: str,
    detail_label: str,
    current_result_context,
    ad_copy_enabled: bool,
    copy_mode: str,
) -> None:
    if generate:
        if not uploaded_file:
            st.warning("메뉴 사진을 먼저 업로드해주세요.")
        else:
            try:
                time.sleep(1.2)
                if FRONTEND_USE_MOCK:
                    mock_copy = ad_copy_prompt.strip() if ad_copy_enabled else ""
                    result = GenerationResult(
                        image_bytes=create_mock_banner(
                            image_bytes=uploaded_file.getvalue(),
                            prompt=mock_copy,
                            format_label=format_label,
                            detail_label=detail_label,
                            ad_copy_enabled=ad_copy_enabled,
                        ),
                        copy=(
                            _mock_copy_info(mock_copy, copy_mode)
                            if ad_copy_enabled and mock_copy
                            else None
                        ),
                    )
                else:
                    # 로그인 상태면 백엔드가 user_id로 기록을 묶을 수 있도록 JWT를 같이 넘긴다.
                    access_token = st.session_state.get("auth_access_token", "")
                    result = request_backend(
                        uploaded_file,
                        prompt.strip(),
                        format_label,
                        detail_label,
                        access_token=access_token,
                        ad_copy_enabled=ad_copy_enabled,
                        copy_mode=copy_mode,
                        ad_copy_prompt=ad_copy_prompt,
                        logo_file=logo_file,
                    )
                st.session_state["result_bytes"] = result.image_bytes
                st.session_state["result_copy"] = result.copy
                st.session_state["result_context"] = current_result_context
                st.rerun()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text
                st.error(f"백엔드 생성 요청 실패 [HTTP {exc.response.status_code}]: {detail}")
            except httpx.HTTPError as exc:
                st.error(
                    f"백엔드 연결 실패 [NETWORK_ERROR] {BACKEND_URL}: {type(exc).__name__}: {exc}"
                )
            except Exception as exc:
                st.error(f"이미지 생성 중 오류가 발생했습니다: {exc}")
