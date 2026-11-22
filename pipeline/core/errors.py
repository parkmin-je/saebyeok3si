"""오류 분류 (ARCHITECTURE.md §5.1)."""


class PipelineError(Exception):
    exit_code = 3


class TransientError(PipelineError):
    """네트워크·타임아웃·429/5xx. 재시도 대상."""
    exit_code = 2

    def __init__(self, msg: str, retry_after: float | None = None):
        super().__init__(msg)
        self.retry_after = retry_after


class ProviderError(PipelineError):
    """재시도 한도를 넘긴 공급자 장애. 폴백 체인의 다음 공급자로."""
    exit_code = 2


class QualityError(PipelineError):
    exit_code = 1

    def __init__(self, code: str, msg: str):
        super().__init__(f"{code}: {msg}")
        self.code = code


class ValidationError(QualityError):
    def __init__(self, msg: str):
        super().__init__("SCHEMA_INVALID", msg)


class BudgetError(PipelineError):
    exit_code = 4


class FatalError(PipelineError):
    """인증 실패, 설정 오류, 쿼터 소진, 정책 위반. 자동 재시도 금지."""
    exit_code = 3
