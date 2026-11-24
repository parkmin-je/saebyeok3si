"""원자적 파일 쓰기와 해시."""
import hashlib
import json
import os
from pathlib import Path


def atomic_write(path: Path, data: bytes | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(tmp, mode, **({} if isinstance(data, bytes) else {"encoding": "utf-8"})) as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    return path


def write_json(path: Path, obj) -> Path:
    return atomic_write(path, json.dumps(obj, ensure_ascii=False, indent=2))


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
