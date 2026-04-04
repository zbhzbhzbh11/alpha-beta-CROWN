import re
from pathlib import Path

import pandas as pd

ROOT_DIR = Path("/home/han/alpha-beta-CROWN")
LOG_DIR = ROOT_DIR / "项目书/results/m4/logs"
OUT_CSV = ROOT_DIR / "项目书/results/m4/m4_epsilon_grid.csv"

FINAL_ACC_RE = re.compile(r"Final verified acc:\s*([0-9]*\.?[0-9]+)%", re.IGNORECASE)
COUNT_RE = re.compile(
    r"Problem instances count:\s*(\d+)\s*,\s*total verified \(safe/unsat\):\s*(\d+)\s*,\s*"
    r"total falsified \(unsafe/sat\):\s*(\d+)\s*,\s*timeout:\s*(\d+)",
    re.IGNORECASE,
)
TIME_RE = re.compile(
    r"mean time for ALL instances \(total\s*\d+\):\s*([0-9]*\.?[0-9]+)\s*,\s*max time:\s*([0-9]*\.?[0-9]+)",
    re.IGNORECASE,
)
NAME_RE = re.compile(r"(baseline|auto|kfsb)_eps([0-9.]+)\.log$")


def parse_log(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    acc = FINAL_ACC_RE.search(text)
    cnt = COUNT_RE.search(text)
    time_matches = TIME_RE.findall(text)

    if not acc or not cnt or not time_matches:
        raise ValueError(f"Failed to parse metrics from {path}")

    mean_t, max_t = time_matches[-1]
    return {
        "verified_acc": float(acc.group(1)),
        "safe": int(cnt.group(2)),
        "unsafe": int(cnt.group(3)),
        "timeout": int(cnt.group(4)),
        "mean_time_s": float(mean_t),
        "max_time_s": float(max_t),
    }


def main():
    rows = []
    for log_path in sorted(LOG_DIR.glob("*.log")):
        m = NAME_RE.search(log_path.name)
        if not m:
            continue
        strategy = m.group(1)
        epsilon = float(m.group(2))
        metrics = parse_log(log_path)
        rows.append(
            {
                "strategy": strategy,
                "epsilon": epsilon,
                **metrics,
                "log_path": str(log_path),
            }
        )

    if not rows:
        raise SystemExit("No M4 logs found")

    df = pd.DataFrame(rows).sort_values(["strategy", "epsilon"])
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    print(f"[OK] Summary CSV: {OUT_CSV}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
