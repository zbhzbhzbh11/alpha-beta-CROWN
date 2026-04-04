import re
from pathlib import Path

import pandas as pd

ROOT_DIR = Path("/home/han/alpha-beta-CROWN")
LOG_DIR = ROOT_DIR / "项目书/results/m3/logs"
OUT_CSV = ROOT_DIR / "项目书/results/m3/m3_branching_ablation.csv"

CONFIG_MAP = {
    "baseline": "mnist_m3_baseline.yaml",
    "auto": "mnist_m3_auto.yaml",
    "kfsb": "mnist_m3_kfsb.yaml",
    "kfsb_reduceop_max": "mnist_m3_kfsb_reduceop_max.yaml",
    "kfsb_candidates5": "mnist_m3_kfsb_candidates5.yaml",
}

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


def parse_log(log_path: Path):
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    acc_match = FINAL_ACC_RE.search(text)
    count_match = COUNT_RE.search(text)
    time_matches = TIME_RE.findall(text)

    if not acc_match or not count_match or not time_matches:
        raise ValueError(f"Failed to parse metrics from {log_path}")

    mean_time, max_time = time_matches[-1]
    return {
        "verified_acc": float(acc_match.group(1)),
        "safe": int(count_match.group(2)),
        "unsafe": int(count_match.group(3)),
        "timeout": int(count_match.group(4)),
        "mean_time_s": float(mean_time),
        "max_time_s": float(max_time),
    }


def main():
    rows = []
    for run_id, config_name in CONFIG_MAP.items():
        log_path = LOG_DIR / f"{run_id}.log"
        if not log_path.exists():
            print(f"[WARN] missing log, skip: {log_path}")
            continue
        metrics = parse_log(log_path)
        rows.append({
            "run_id": run_id,
            "config": config_name,
            **metrics,
            "log_path": str(log_path),
        })

    if not rows:
        raise SystemExit("No logs found to summarize")

    df = pd.DataFrame(rows)
    df = df.sort_values("run_id")
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    print(f"[OK] Summary CSV: {OUT_CSV}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
