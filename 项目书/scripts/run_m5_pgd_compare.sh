#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/han/alpha-beta-CROWN"
CV_DIR="${ROOT_DIR}/complete_verifier"
CFG_DIR="${CV_DIR}/exp_configs/course/m5_pgd"
LOG_DIR="${ROOT_DIR}/项目书/results/m5_pgd/logs"
META_DIR="${ROOT_DIR}/项目书/results/m5_pgd/meta"
CHUNK_DIR="${LOG_DIR}/chunks"
PYTHON_BIN="/home/han/miniconda3/envs/alpha-beta-crown/bin/python"

export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-4}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-4}"

mkdir -p "${LOG_DIR}" "${META_DIR}" "${CHUNK_DIR}"

strategies=("baseline" "kfsb")
epsilons=("0.01" "0.02" "0.03" "0.05")

run_chunked() {
  local run_id="$1"
  local cfg_path="$2"
  local log_path="$3"
  local meta_path="$4"
  local chunk_size=10
  local batch_size=64
  local timeout_sec=12

  local chunk_dir="${CHUNK_DIR}/${run_id}"
  mkdir -p "${chunk_dir}"

  local start=0
  while [[ ${start} -lt 100 ]]; do
    local end=$((start + chunk_size))
    local chunk_log="${chunk_dir}/${run_id}_${start}_${end}.log"

    if [[ -f "${chunk_log}" ]] && grep -q "Final verified acc:" "${chunk_log}"; then
      echo "[SKIP-CHUNK] ${run_id} ${start}-${end}"
      start=${end}
      continue
    fi

    echo "[RUN-CHUNK] ${run_id} ${start}-${end}"
    set +e
    /usr/bin/time -f "wall_time_sec=%e\nmax_rss_kb=%M" -o "${meta_path}" -a \
      "${PYTHON_BIN}" abcrown.py --config "${cfg_path}" \
      --start "${start}" --end "${end}" \
      --batch_size "${batch_size}" --timeout "${timeout_sec}" \
      --mip_multi_proc 2 --mip_threads 1 --mip_perneuron_refine_timeout 5 \
      > "${chunk_log}" 2>&1
    local rc=$?
    set -e

    echo "chunk_${start}_${end}_exit_code=${rc}" >> "${meta_path}"
    if [[ ${rc} -ne 0 ]]; then
      echo "[FAIL-CHUNK] ${run_id} ${start}-${end} exit_code=${rc}"
      return ${rc}
    fi

    start=${end}
  done

  # Aggregate chunk summaries
  "${PYTHON_BIN}" - "$(printf '%s' "${chunk_dir}")" "$(printf '%s' "${run_id}")" "$(printf '%s' "${log_path}")" <<'PY'
import re
import sys
from pathlib import Path

chunk_dir = Path(sys.argv[1])
run_id = sys.argv[2]
out_log = Path(sys.argv[3])

acc_re = re.compile(r"Final verified acc:\s*([0-9]*\.?[0-9]+)%\s*\(total\s*(\d+)\s*examples\)")
cnt_re = re.compile(
    r"Problem instances count:\s*(\d+)\s*,\s*total verified \(safe/unsat\):\s*(\d+)\s*,\s*"
    r"total falsified \(unsafe/sat\):\s*(\d+)\s*,\s*timeout:\s*(\d+)")
time_re = re.compile(r"mean time for ALL instances \(total\s*\d+\):\s*([0-9]*\.?[0-9]+)\s*,\s*max time:\s*([0-9]*\.?[0-9]+)")

total = safe = unsafe = timeout = 0
weighted_time = 0.0
max_time = 0.0
pgd_unsafe_total = 0

status_re = re.compile(r"^(unsafe-pgd|unsafe-bab|unsafe|safe|unknown)\s*\(total\s*(\d+)\)")

for p in sorted(chunk_dir.glob("*.log")):
    text = p.read_text(encoding="utf-8", errors="ignore")
    m_acc = acc_re.search(text)
    m_cnt = cnt_re.search(text)
    m_time = time_re.search(text)
    if not (m_acc and m_cnt and m_time):
        continue
    n = int(m_cnt.group(1))
    s = int(m_cnt.group(2))
    u = int(m_cnt.group(3))
    t = int(m_cnt.group(4))
    mean_t = float(m_time.group(1))
    max_t = float(m_time.group(2))

    total += n
    safe += s
    unsafe += u
    timeout += t
    weighted_time += mean_t * n
    max_time = max(max_time, max_t)

    for m in status_re.finditer(text):
        if m.group(1) == "unsafe-pgd":
            pgd_unsafe_total += int(m.group(2))

if total == 0:
    out_log.write_text(f"[ERROR] No valid chunk summaries for {run_id}\n", encoding="utf-8")
    sys.exit(2)

final_acc = 100.0 * safe / total
mean_time = weighted_time / total

lines = [
    "############# Summary #############",
    f"Final verified acc: {final_acc:.1f}% (total {total} examples)",
    f"Problem instances count: {total} , total verified (safe/unsat): {safe} , total falsified (unsafe/sat): {unsafe} , timeout: {timeout}",
    f"mean time for ALL instances (total {total}):{mean_time}, max time: {max_time}",
    f"unsafe-pgd (total {pgd_unsafe_total}), index: []",
    f"safe (total {safe}), index: []",
    f"unknown (total {timeout}), index: []",
    "",
]
out_log.write_text("\n".join(lines), encoding="utf-8")
PY
}

cd "${CV_DIR}"

for s in "${strategies[@]}"; do
  for e in "${epsilons[@]}"; do
    run_id="${s}_eps${e}"
    cfg_path="${CFG_DIR}/mnist_m5pgd_${s}_eps${e}.yaml"
    log_path="${LOG_DIR}/${run_id}.log"
    meta_path="${META_DIR}/${run_id}.txt"

    if [[ ! -f "${cfg_path}" ]]; then
      echo "[WARN] missing config: ${cfg_path}"
      continue
    fi

    if [[ -f "${log_path}" ]] && grep -q "Final verified acc:" "${log_path}"; then
      echo "[SKIP] ${run_id} already completed"
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
    echo "threads: OMP=${OMP_NUM_THREADS}, MKL=${MKL_NUM_THREADS}, OPENBLAS=${OPENBLAS_NUM_THREADS}" >> "${meta_path}"

    if [[ "${e}" == "0.03" || "${e}" == "0.05" ]]; then
      # Chunked execution to avoid WSL resource exhaustion.
      # 0.03 and 0.05 both stress the WSL VM with PGD + BaB combined load.
      set +e
      run_chunked "${run_id}" "${cfg_path}" "${log_path}" "${meta_path}"
      rc=$?
      set -e
    else
      set +e
      /usr/bin/time -f "wall_time_sec=%e\nmax_rss_kb=%M" -o "${meta_path}" -a \
        "${PYTHON_BIN}" abcrown.py --config "${cfg_path}" > "${log_path}" 2>&1
      rc=$?
      set -e
    fi

    echo "exit_code=${rc}" >> "${meta_path}"
    if [[ ${rc} -ne 0 ]]; then
      echo "[FAIL] ${run_id} exit_code=${rc}"
      continue
    fi

    if grep -q "Final verified acc:" "${log_path}"; then
      echo "[OK] ${run_id} completed"
    else
      echo "[WARN] ${run_id} finished without summary"
    fi
  done
done

echo "[DONE] logs written to ${LOG_DIR}"
