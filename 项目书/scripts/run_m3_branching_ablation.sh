#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/han/alpha-beta-CROWN"
CV_DIR="${ROOT_DIR}/complete_verifier"
CFG_DIR="${CV_DIR}/exp_configs/course/m3"
LOG_DIR="${ROOT_DIR}/项目书/results/m3/logs"
META_DIR="${ROOT_DIR}/项目书/results/m3/meta"

mkdir -p "${LOG_DIR}" "${META_DIR}"

runs=(
  "baseline:mnist_m3_baseline.yaml"
  "auto:mnist_m3_auto.yaml"
  "kfsb:mnist_m3_kfsb.yaml"
  "kfsb_reduceop_max:mnist_m3_kfsb_reduceop_max.yaml"
  "kfsb_candidates5:mnist_m3_kfsb_candidates5.yaml"
)

PYTHON_BIN="/home/han/miniconda3/envs/alpha-beta-crown/bin/python"

cd "${CV_DIR}"

for item in "${runs[@]}"; do
  IFS=":" read -r run_id config_name <<< "${item}"
  cfg_path="${CFG_DIR}/${config_name}"
  log_path="${LOG_DIR}/${run_id}.log"
  meta_path="${META_DIR}/${run_id}.txt"

  if [[ ! -f "${cfg_path}" ]]; then
    echo "[WARN] missing config: ${cfg_path}"
    continue
  fi

  {
    echo "run_id=${run_id}"
    echo "config=${cfg_path}"
    echo "timestamp=$(date '+%F %T')"
    echo "hostname=$(hostname)"
    echo "python=$(${PYTHON_BIN} -V 2>&1)"
  } > "${meta_path}"

  echo "[RUN] ${run_id}"
  /usr/bin/time -f "wall_time_sec=%e\nmax_rss_kb=%M" \
    "${PYTHON_BIN}" abcrown.py --config "${cfg_path}" 2>&1 | tee "${log_path}" >> "${meta_path}"
done

echo "[DONE] logs written to ${LOG_DIR}"
