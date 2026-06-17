"""API 요청/응답 스키마."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.core.presets import Preset

ResizeMode = Literal["cover", "contain"]
CopyMode = Literal["preserve", "polish", "rewrite"]


class ConfigResponse(BaseModel):
    """프론트 초기 설정에 필요한 프리셋과 provider 정보."""

    presets: list[Preset]
    provider: str
    max_upload_bytes: int = Field(alias="maxUploadBytes")


class GenerateRequest(BaseModel):
    """이미지 생성 요청 본문."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    image_data_url: str = Field(alias="imageDataUrl")
    preset_id: str | None = Field(default=None, alias="presetId")
    detail_type: str | None = Field(default=None, alias="detailType")
    user_prompt: str = Field(default="", alias="userPrompt")
    copy_mode: CopyMode = Field(default="preserve", alias="copyMode")
    ad_copy_enabled: bool = Field(default=False, alias="adCopyEnabled")
    user_copy: str | None = Field(default=None, alias="userCopy", max_length=300)
    parent_request_id: str | None = Field(default=None, alias="parentRequestId")
    target_width: int | None = Field(default=None, alias="targetWidth", ge=1, le=4096)
    target_height: int | None = Field(default=None, alias="targetHeight", ge=1, le=4096)
    resize_mode: ResizeMode = Field(default="cover", alias="resizeMode")

    @model_validator(mode="after")
    def validate_target_size(self) -> "GenerateRequest":
        """최종 출력 크기는 너비와 높이를 한 쌍으로만 받는다."""
        if (self.target_width is None) != (self.target_height is None):
            raise ValueError("targetWidth와 targetHeight는 함께 전달해야 합니다.")
        return self


class CopyGenerateRequest(BaseModel):
    """광고 문구 자동 생성 요청 본문."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    preset_id: str | None = Field(default=None, alias="presetId")
    detail_type: str | None = Field(default=None, alias="detailType")
    user_prompt: str = Field(default="", alias="userPrompt")
    copy_mode: CopyMode = Field(default="rewrite", alias="copyMode")


class CopyResponse(BaseModel):
    """V3 문구 처리 결과. 이미지 프롬프트에 포함할 광고 문구를 담는다."""

    model_config = ConfigDict(populate_by_name=True)

    headline: str | None = None
    subcopy: str | None = None
    cta: str | None = None
    mode: CopyMode | None = Field(default=None, alias="copyMode")


class RevisionResponse(BaseModel):
    """V3 수정 이력 정보. 최초 생성이면 parentRequestId는 null이다."""

    model_config = ConfigDict(populate_by_name=True)

    parent_request_id: str | None = Field(default=None, alias="parentRequestId")
    revision_number: int | None = Field(default=None, alias="revisionNumber")


class GenerateResponse(BaseModel):
    """이미지 생성 응답 본문."""

    model_config = ConfigDict(populate_by_name=True)

    # 저장 URL을 우선 사용한다. imageDataUrl은 mock/fallback처럼 URL이 없을 때만 내려준다.
    image_data_url: str | None = Field(default=None, alias="imageDataUrl")
    image_url: str | None = Field(default=None, alias="imageUrl")
    download_url: str | None = Field(default=None, alias="downloadUrl")
    provider: str
    preset: Preset
    copy_info: CopyResponse | None = Field(default=None, alias="copy")
    revision_info: RevisionResponse | None = Field(default=None, alias="revision")
    note: str | None = None
    prompt: str | None = None


class GenerateJobCreateResponse(BaseModel):
    """비동기 이미지 생성 job 생성 응답."""

    model_config = ConfigDict(populate_by_name=True)

    request_id: str = Field(alias="requestId")
    job_id: str = Field(alias="jobId")
    status: str


class GenerateJobStatusResponse(BaseModel):
    """비동기 이미지 생성 job 상태 조회 응답."""

    model_config = ConfigDict(populate_by_name=True)

    request_id: str = Field(alias="requestId")
    job_id: str = Field(alias="jobId")
    status: str
    image_url: str | None = Field(default=None, alias="imageUrl")
    original_image_url: str | None = Field(default=None, alias="originalImageUrl")
    copy_info: CopyResponse | None = Field(default=None, alias="copy")
    error: str | None = None
    created_at: str | None = Field(default=None, alias="createdAt")
    updated_at: str | None = Field(default=None, alias="updatedAt")
