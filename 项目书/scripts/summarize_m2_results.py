import re
from pathlib import Path
import pandas as pd

ROOT_DIR = Path("/home/han/alpha-beta-CROWN")
DEFAULT_LOG_DIR = ROOT_DIR / "项目书/results/m2/logs"
LEGACY_LOG_DIR = ROOT_DIR / "项目书/实验日志"
OUT_CSV = ROOT_DIR / "项目书/results/m2/m2_strategy_compare_0_100.csv"

LOG_PATTERN = re.compile(r"m2_(baseline|auto|kfsb)_0_100\.log$")
LEGACY_MAP = {
    "baseline": "2026-03-14_mnist_baseline_0_100.log",
    "auto": "2026-03-14_mnist_auto_0_100.log",
    "kfsb": "2026-03-14_mnist_kfsb_0_100.log",
}

FINAL_ACC_RE = re.compile(r"Final verified acc:\s*([0-9]*\.?[0-9]+)%")
COUNT_RE = re.compile(
    r"Problem instances count:\s*(\d+)\s*,\s*total verified \(safe/unsat\):\s*(\d+)\s*,\s*"
    r"total falsified \(unsafe/sat\):\s*(\d+)\s*,\s*timeout:\s*(\d+)")
TIME_RE = re.compile(
    r"mean time for ALL instances \(total\s*\d+\):\s*([0-9]*\.?[0-9]+)\s*,\s*max time:\s*([0-9]*\.?[0-9]+)",
    re.IGNORECASE,
)

CONFIG_MAP = {
    "baseline": "mnist_baseline.yaml",
    "auto": "mnist_baseline_auto.yaml",
    "kfsb": "mnist_baseline_kfsb.yaml",
}


def parse_log(log_path: Path):
    text = log_path.read_text(encoding="utf-8", errors="ignore")

    acc_m = FINAL_ACC_RE.search(text)
    cnt_m = COUNT_RE.search(text)
    time_matches = TIME_RE.findall(text)

    if not acc_m or not cnt_m or not time_matches:
        raise ValueError(f"Failed to parse key metrics from {log_path}")

    mean_time, max_time = time_matches[-1]
    return {
        "verified_acc": float(acc_m.group(1)),
        "safe": int(cnt_m.group(2)),
        "unsafe": int(cnt_m.group(3)),
        "timeout": int(cnt_m.group(4)),
        "mean_time_s": float(mean_time),
        "max_time_s": float(max_time),
    }


def resolve_logs():
    logs = {}

    if DEFAULT_LOG_DIR.exists():
        for p in DEFAULT_LOG_DIR.glob("m2_*_0_100.log"):
            m = LOG_PATTERN.search(p.name)
            if m:
                logs[m.group(1)] = p

    for run_id, legacy_name in LEGACY_MAP.items():
        if run_id not in logs:
            legacy_path = LEGACY_LOG_DIR / legacy_name
            if legacy_path.exists():
                logs[run_id] = legacy_path

    missing = [k for k in ["baseline", "auto", "kfsb"] if k not in logs]
    if missing:
        raise FileNotFoundError(f"Missing logs for: {missing}")

    return logs


def main():
    logs = resolve_logs()
    rows = []

    for run_id in ["baseline", "auto", "kfsb"]:
        metrics = parse_log(logs[run_id])
        rows.append({
            "run_id": run_id,
            "config": CONFIG_MAP[run_id],
            **metrics,
            "log_path": str(logs[run_id]),
        })

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    print(f"[OK] Summary CSV: {OUT_CSV}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
