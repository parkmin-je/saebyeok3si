"""스테이지 공통: 실행 컨텍스트, 인물 치환, 시드."""
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..core.errors import BudgetError

KEY_RE = re.compile(r"\{([A-Z])\}")


@dataclass
class Ctx:
    run_dir: Path
    repo: Path
    script: dict
    cfg: dict
    providers: dict
    budget_usd: float
    spent_usd: float = 0.0
    meta: dict = field(default_factory=dict)

    def log(self, msg: str) -> None:
        print(msg, flush=True)
        with open(self.run_dir / "logs.txt", "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    def charge(self, usd: float, what: str) -> None:
        self.spent_usd += usd
        self.log(f"[cost] {what}: ${usd:.3f} (누적 ${self.spent_usd:.2f} / 상한 ${self.budget_usd:.2f})")
        if self.spent_usd > self.budget_usd:
            raise BudgetError(f"편당 예산 초과: ${self.spent_usd:.2f}")


def looks(script: dict) -> dict[str, str]:
    return {c["key"]: c["look"] for c in script["characters"]}


def keys_in(prompt: str) -> list[str]:
    return sorted(set(KEY_RE.findall(prompt)))


def fill(prompt: str, script: dict) -> str:
    lk = looks(script)
    return KEY_RE.sub(lambda m: lk[m.group(1)], prompt)


def seed_for(*parts) -> int:
    return int(hashlib.sha256(json.dumps(parts).encode()).hexdigest()[:8], 16) % 2_147_483_647


def nn(no: int) -> str:
    return f"{no:02d}"
