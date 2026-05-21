"""DB 저장·조회 로직."""

import uuid

from sqlalchemy.orm import Session

from app.db import models


def create_generation(
    db: Session,
    original_image_path: str,
    ad_copy: str,
    generated_image_path: str | None = None,
    prompt: str | None = None,
) -> models.Generation:
    """새 세션과 생성 기록을 DB에 저장한다.

    Args:
        db: DB 세션.
        original_image_path: 업로드된 원본 이미지 경로.
        ad_copy: 생성된 광고 문구.
        generated_image_path: 생성된 이미지 경로(없으면 None).
        prompt: 이미지 생성 프롬프트(없으면 None).
    Returns:
        저장된 Generation 객체(생성된 session_id 포함).
    """
    session_id = uuid.uuid4().hex
    db.add(models.WorkSession(session_id=session_id))
    db.flush()  # 부모(sessions) 행을 먼저 DB에 보내 FK 제약을 충족시킨다
    gen = models.Generation(
        session_id=session_id,
        original_image_path=original_image_path,
        generated_image_path=generated_image_path,
        ad_copy=ad_copy,
        prompt=prompt,
    )
    db.add(gen)
    db.commit()
    db.refresh(gen)
    return gen
