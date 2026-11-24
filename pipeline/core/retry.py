"""지수 백오프 재시도 (일시 오류만)."""
import random
import time
from typing import Callable, TypeVar

from .errors import ProviderError, TransientError

T = TypeVar("T")


def with_retry(fn: Callable[[], T], *, max_attempts: int = 5, base_sec: float = 2,
               max_sec: float = 60, log=print, label: str = "") -> T:
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except TransientError as e:
            if attempt == max_attempts:
                raise ProviderError(f"{label}: 재시도 {max_attempts}회 실패: {e}") from e
            wait = e.retry_after or min(max_sec, base_sec * 2 ** (attempt - 1))
            wait += random.uniform(0, wait * 0.2)
            log(f"[retry] {label} {attempt}/{max_attempts} 실패 ({e}); {wait:.1f}s 후 재시도")
            time.sleep(wait)
    raise AssertionError("unreachable")
