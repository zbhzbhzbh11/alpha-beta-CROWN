import re
from pathlib import Path

import pandas as pd

ROOT = Path("/home/han/alpha-beta-CROWN")
LOG_DIR = ROOT / "项目书/results/m3/logs"
OUT = ROOT / "项目书/results/m3/m3_nodes_summary.csv"

RUNS = ["baseline", "auto", "kfsb", "kfsb_reduceop_max", "kfsb_candidates5"]

RE_NODES = re.compile(r"(\d+)\s+domains visited", re.IGNORECASE)
RE_ACC = re.compile(r"Final verified acc:\s*([0-9]*\.?[0-9]+)%", re.IGNORECASE)
RE_TIMEOUT = re.compile(
    r"Problem instances count:\s*(\d+)\s*,\s*total verified \(safe/unsat\):\s*(\d+)\s*,\s*"
    r"total falsified \(unsafe/sat\):\s*(\d+)\s*,\s*timeout:\s*(\d+)",
    re.IGNORECASE,
)


def parse_log(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")

    nodes = [int(x) for x in RE_NODES.findall(text)]
    acc = RE_ACC.search(text)
    timeout = RE_TIMEOUT.search(text)

    return {
        "domains_visited_last": nodes[-1] if nodes else None,
        "domains_visited_max": max(nodes) if nodes else None,
        "verified_acc": float(acc.group(1)) if acc else None,
        "timeout": int(timeout.group(4)) if timeout else None,
    }


def main():
    rows = []
    for run in RUNS:
        p = LOG_DIR / f"{run}.log"
        if not p.exists():
            continue
        rows.append({"run_id": run, **parse_log(p), "log_path": str(p)})

    df = pd.DataFrame(rows).sort_values("run_id")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"[OK] {OUT}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
