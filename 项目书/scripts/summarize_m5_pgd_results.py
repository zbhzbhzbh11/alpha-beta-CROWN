#!/usr/bin/env python3
"""
Summarize M5 PGD attack evaluation experiment results.

Parses verification logs for each (strategy, epsilon) combination and produces
a CSV with PGD attack stats separated from BaB verification stats.

Output columns:
  epsilon, strategy, total_samples,
  pgd_unsafe_count, bab_safe_count, bab_unsafe_count, bab_unknown_count,
  final_verified_acc, mean_time, timeout_count

Usage:
  python 项目书/scripts/summarize_m5_pgd_results.py
"""

import re
import csv
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR.parent / "results" / "m5_pgd"
LOG_DIR = RESULTS_DIR / "logs"
OUTPUT_CSV = RESULTS_DIR / "m5_pgd_compare.csv"


def parse_log(log_path: Path) -> dict | None:
    """Parse a verification log and extract PGD + BaB metrics."""
    if not log_path.exists():
        print(f"  [WARN] missing log: {log_path}")
        return None

    text = log_path.read_text(encoding="utf-8", errors="ignore")

    # Summary line
    cnt_re = re.compile(
        r"Problem instances count:\s*(\d+)\s*,\s*"
        r"total verified \(safe/unsat\):\s*(\d+)\s*,\s*"
        r"total falsified \(unsafe/sat\):\s*(\d+)\s*,\s*"
        r"timeout:\s*(\d+)"
    )
    time_re = re.compile(
        r"mean time for ALL instances \(total\s*\d+\):\s*([0-9]*\.?[0-9]+)"
    )

    m_cnt = cnt_re.search(text)
    m_time = time_re.search(text)

    if not m_cnt:
        print(f"  [WARN] no summary found in: {log_path}")
        return None

    total_samples = int(m_cnt.group(1))
    safe_count = int(m_cnt.group(2))
    total_unsafe = int(m_cnt.group(3))
    timeout_count = int(m_cnt.group(4))
    mean_time = float(m_time.group(1)) if m_time else 0.0

    # Parse per-status lines to separate PGD-unsafe from BaB-unsafe.
    # Status strings include: safe, safe-incomplete, unsafe, unsafe-pgd,
    # unsafe-bab, unknown, and variants with " (timed out)" suffix.
    status_re = re.compile(r"^([a-z][-a-z ]*?)\s*\(total\s*(\d+)\)", re.MULTILINE)
    status_counts: dict[str, int] = {}
    for m in status_re.finditer(text):
        key = m.group(1).strip()
        status_counts[key] = status_counts.get(key, 0) + int(m.group(2))

    # Classify by semantic category
    pgd_unsafe_count = status_counts.get("unsafe-pgd", 0)
    bab_safe_count = sum(
        v for k, v in status_counts.items()
        if "safe" in k and "unsafe" not in k
    )
    bab_unsafe_count = sum(
        v for k, v in status_counts.items()
        if "unsafe" in k and "pgd" not in k
    )
    bab_unknown_count = sum(
        v for k, v in status_counts.items()
        if "unknown" in k
    )

    # Fallback to summary-line counts if per-status parsing yields zero
    if bab_safe_count == 0:
        bab_safe_count = safe_count
    if bab_unknown_count == 0:
        bab_unknown_count = timeout_count

    if total_samples > 0:
        final_verified_acc = 100.0 * bab_safe_count / total_samples
    else:
        final_verified_acc = 0.0

    return {
        "total_samples": total_samples,
        "pgd_unsafe_count": pgd_unsafe_count,
        "bab_safe_count": bab_safe_count,
        "bab_unsafe_count": bab_unsafe_count,
        "bab_unknown_count": bab_unknown_count,
        "final_verified_acc": round(final_verified_acc, 1),
        "mean_time": round(mean_time, 4),
        "timeout_count": timeout_count,
    }


def extract_epsilon(run_id: str) -> str:
    """Extract epsilon value from run_id like 'baseline_eps0.02'."""
    m = re.search(r"eps(\d+\.\d+)", run_id)
    return m.group(1) if m else "?"


def extract_strategy(run_id: str) -> str:
    """Extract strategy name from run_id like 'baseline_eps0.02'."""
    return run_id.rsplit("_eps", 1)[0]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Summarize M5 PGD experiment results")
    parser.add_argument("--output", type=Path, default=OUTPUT_CSV,
                        help="Output CSV path")
    parser.add_argument("--suffix", type=str, default="",
                        help="Log filename suffix (e.g. '_smoke10' for smoke test logs)")
    parser.add_argument("--epsilons", type=str, default="0.01,0.02,0.03,0.05",
                        help="Comma-separated epsilon list")
    parser.add_argument("--strategies", type=str, default="baseline,kfsb",
                        help="Comma-separated strategy list")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    strategies = args.strategies.split(",")
    epsilons = args.epsilons.split(",")
    output_csv = args.output
    suffix = args.suffix

    experiments = [
        (f"{s}_eps{e}", f"mnist_m5pgd_{s}_eps{e}.yaml")
        for s in strategies
        for e in epsilons
    ]

    results = []
    for run_id, config in experiments:
        log_path = LOG_DIR / f"{run_id}{suffix}.log"
        chunk_dir = LOG_DIR / "chunks" / run_id

        # Use chunked log if it exists and the main log doesn't
        actual_log = log_path
        if not log_path.exists() and chunk_dir.exists():
            actual_log = log_path  # chunked execution writes synthetic log here

        print(f"Parsing: {run_id}")
        metrics = parse_log(actual_log)

        if metrics is None:
            print(f"  [SKIP] {run_id}: no valid data")
            continue

        results.append({
            "epsilon": extract_epsilon(run_id),
            "strategy": extract_strategy(run_id),
            "config": config,
            **metrics,
            "log_path": str(log_path.relative_to(SCRIPT_DIR.parent.parent)),
        })
        print(f"  eps={extract_epsilon(run_id)} "
              f"total={metrics['total_samples']} "
              f"pgd_unsafe={metrics['pgd_unsafe_count']} "
              f"bab_safe={metrics['bab_safe_count']} "
              f"bab_unsafe={metrics['bab_unsafe_count']} "
              f"bab_unknown={metrics['bab_unknown_count']} "
              f"vra={metrics['final_verified_acc']}% "
              f"timeout={metrics['timeout_count']}")

    # Write CSV
    fieldnames = [
        "epsilon", "strategy", "config",
        "total_samples",
        "pgd_unsafe_count", "bab_safe_count", "bab_unsafe_count", "bab_unknown_count",
        "final_verified_acc", "mean_time", "timeout_count",
        "log_path",
    ]
    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nCSV written to: {output_csv}")
    print(f"Total rows: {len(results)}")

    # Print summary table
    print(f"\n{'epsilon':<8} {'strategy':<12} {'total':<6} "
          f"{'pgd_u':<6} {'bab_s':<6} {'bab_u':<6} {'unk':<6} "
          f"{'VRA%':<8} {'mean_t':<10} {'t/o':<5}")
    print("-" * 85)
    for r in sorted(results, key=lambda x: (float(x["epsilon"]), x["strategy"])):
        print(f"{r['epsilon']:<8} {r['strategy']:<12} {r['total_samples']:<6} "
              f"{r['pgd_unsafe_count']:<6} {r['bab_safe_count']:<6} "
              f"{r['bab_unsafe_count']:<6} {r['bab_unknown_count']:<6} "
              f"{r['final_verified_acc']:<8.1f} {r['mean_time']:<10.2f} {r['timeout_count']:<5}")


if __name__ == "__main__":
    main()
