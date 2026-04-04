#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/han/alpha-beta-CROWN"
CV_DIR="${ROOT_DIR}/complete_verifier"
LOG_DIR="${ROOT_DIR}/项目书/results/m2/logs"

mkdir -p "${LOG_DIR}"

# M2 fixed protocol: MNIST, epsilon=0.02, sample range 0-100.
runs=(
  "baseline::mnist_baseline.yaml::bab::babsr"
  "auto::exp_configs/course/mnist_baseline_auto.yaml::auto::babsr"
  "kfsb::exp_configs/course/mnist_baseline_kfsb.yaml::bab::kfsb"
)

cd "${CV_DIR}"

for item in "${runs[@]}"; do
  IFS="::" read -r run_id config verifier branching <<< "${item}"
  log_file="${LOG_DIR}/m2_${run_id}_0_100.log"

  echo "[RUN] ${run_id}"
  python abcrown.py \
    --config "${config}" \
    --start 0 \
    --end 100 \
    --complete_verifier "${verifier}" \
    --branching_method "${branching}" \
    2>&1 | tee "${log_file}"
done

echo "[DONE] Logs written to ${LOG_DIR}"
