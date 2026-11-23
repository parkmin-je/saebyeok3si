"""Modal 계정에서 카드 없이 쓸 수 있는 GPU 종류 찾기. 가장 좋은 것을 출력한다."""
import sys

import modal

order = ["H100", "A100-80GB", "L40S", "A100-40GB", "A10G", "L4", "T4"]
ok = []
for g in order:
    app = modal.App(f"rrs-probe-{g.lower()}")

    @app.function(gpu=g, timeout=120, serialized=True)
    def hi():
        import subprocess
        return subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                              capture_output=True, text=True).stdout.strip()

    try:
        with app.run():
            print(g, "OK", hi.remote(), file=sys.stderr, flush=True)
            ok.append(g)
            break
    except Exception as e:  # noqa: BLE001
        print(g, "불가:", str(e)[:120], file=sys.stderr, flush=True)
print(ok[0] if ok else "NONE")
