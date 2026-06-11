"""API 에러 응답을 코드 기반으로 통일하는 보조 타입."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorBody:
    """프론트가 분기 처리할 수 있는 에러 응답 본문."""

    code: str
    message: str

    def to_detail(self) -> dict[str, str]:
        """FastAPI HTTPException.detail에 넣을 dict로 변환한다."""
        return {"code": self.code, "message": self.message}


class ServiceError(RuntimeError):
    """서비스 계층에서 라우터까지 전달하는 코드 기반 예외."""

    def __init__(self, code: str, message: str, *, status_code: int = 503) -> None:
        super().__init__(message)
        self.body = ErrorBody(code=code, message=message)
        self.status_code = status_code

    @property
    def code(self) -> str:
        """프론트/로그에서 사용하는 안정적인 에러 코드."""
        return self.body.code

    @property
    def message(self) -> str:
        """사용자에게 보여줄 수 있는 안전한 에러 메시지."""
        return self.body.message

    def to_detail(self) -> dict[str, str]:
        """HTTPException.detail에 넣을 응답 본문."""
        return self.body.to_detail()


def error_detail(code: str, message: str) -> dict[str, str]:
    """라우터에서 직접 만드는 에러 응답도 같은 형태로 맞춘다."""
    return ErrorBody(code=code, message=message).to_detail()
