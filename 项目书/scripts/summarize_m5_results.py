#!/usr/bin/env python3
"""
Summarize M5 CIFAR-10 experiment results.
"""
import re
import csv
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR.parent / "results" / "m5"
LOG_DIR = RESULTS_DIR / "logs"
OUTPUT_CSV = RESULTS_DIR / "m5_cifar10_compare.csv"

def parse_log(log_path):
    """Parse verification log and extract metrics."""
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Extract final summary
    verified_acc_match = re.search(r'Final verified acc:\s+([\d.]+)%', content)
    safe_match = re.search(r'total verified \(safe/unsat\):\s+(\d+)', content)
    unsafe_match = re.search(r'total falsified \(unsafe/sat\):\s+(\d+)', content)
    timeout_match = re.search(r'Problem instances count:.*?timeout:\s+(\d+)', content)
    mean_time_match = re.search(r'mean time for ALL instances \(total \d+\):\s*([\d.]+)', content)
    max_time_match = re.search(r'mean time for ALL instances.*?max time:\s+([\d.]+)', content)

    return {
        'verified_acc': float(verified_acc_match.group(1)) if verified_acc_match else 0.0,
        'safe': int(safe_match.group(1)) if safe_match else 0,
        'unsafe': int(unsafe_match.group(1)) if unsafe_match else 0,
        'timeout': int(timeout_match.group(1)) if timeout_match else 0,
        'mean_time_s': float(mean_time_match.group(1)) if mean_time_match else 0.0,
        'max_time_s': float(max_time_match.group(1)) if max_time_match else 0.0,
    }

def main():
    experiments = [
        ('cifar10_baseline', 'mnist_cifar10_baseline.yaml'),
        ('cifar10_kfsb_candidates5', 'mnist_cifar10_kfsb.yaml'),
    ]

    results = []
    for run_id, config in experiments:
        log_path = LOG_DIR / f"{run_id}.log"
        if not log_path.exists():
            print(f"Warning: {log_path} not found, skipping")
            continue

        metrics = parse_log(log_path)
        results.append({
            'run_id': run_id,
            'config': config,
            'verified_acc': metrics['verified_acc'],
            'safe': metrics['safe'],
            'unsafe': metrics['unsafe'],
            'timeout': metrics['timeout'],
            'mean_time_s': metrics['mean_time_s'],
            'max_time_s': metrics['max_time_s'],
            'log_path': str(log_path.relative_to(SCRIPT_DIR.parent.parent)),
        })

    # Write CSV
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'run_id', 'config', 'verified_acc', 'safe', 'unsafe', 'timeout',
            'mean_time_s', 'max_time_s', 'log_path'
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults written to: {OUTPUT_CSV}")
    print("\nSummary:")
    print(f"{'run_id':<30} {'VRA':<8} {'safe':<6} {'timeout':<8} {'mean_time(s)':<12}")
    print("-" * 70)
    for r in results:
        print(f"{r['run_id']:<30} {r['verified_acc']:<8.1f} {r['safe']:<6} {r['timeout']:<8} {r['mean_time_s']:<12.2f}")

if __name__ == '__main__':
    main()
