#!/bin/bash
# M5: CIFAR-10 补充实验（小样本，n=0-20）
# 模型：cifar_marabou_small（Conv+ReLU+FC，官方最小CIFAR-10模型）
# 策略：baseline vs kfsb_candidates5
# 目的：验证策略优化在CIFAR-10上的迁移效果

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VERIFIER="$PROJECT_ROOT/complete_verifier"
RESULTS_DIR="$SCRIPT_DIR/../results/m5"
LOG_DIR="$RESULTS_DIR/logs"
META_DIR="$RESULTS_DIR/meta"

mkdir -p "$LOG_DIR" "$META_DIR"

cd "$VERIFIER"

run_exp() {
    local run_id=$1
    local config=$2
    local log_file="$LOG_DIR/${run_id}.log"
    local meta_file="$META_DIR/${run_id}.txt"

    echo "Running $run_id ..."

    # Write meta info
    {
        echo "run_id=$run_id"
        echo "config=$config"
        echo "timestamp=$(date '+%Y-%m-%d %H:%M:%S')"
        echo "hostname=$(hostname)"
        echo "python=$(python3 --version)"
        echo "gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || echo 'N/A')"
    } > "$meta_file"

    start_time=$(date +%s)
    python3 abcrown.py --config "$config" 2>&1 | tee "$log_file"
    exit_code=${PIPESTATUS[0]}
    end_time=$(date +%s)

    echo "wall_time_sec=$((end_time - start_time))" >> "$meta_file"
    echo "exit_code=$exit_code" >> "$meta_file"

    echo "Done $run_id (exit=$exit_code, time=$((end_time - start_time))s)"
}

run_exp "cifar10_baseline" "exp_configs/mnist_cifar10_baseline.yaml"
run_exp "cifar10_kfsb_candidates5" "exp_configs/mnist_cifar10_kfsb.yaml"

echo ""
echo "All CIFAR-10 experiments done. Logs: $LOG_DIR"
echo "Run summarize script next:"
echo "  python3 $SCRIPT_DIR/summarize_m5_results.py"
