#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/han/alpha-beta-CROWN"
CV_DIR="${ROOT_DIR}/complete_verifier"
CFG_DIR="${CV_DIR}/exp_configs/course/m4"
LOG_DIR="${ROOT_DIR}/项目书/results/m4/logs"
META_DIR="${ROOT_DIR}/项目书/results/m4/meta"
PYTHON_BIN="/home/han/miniconda3/envs/alpha-beta-crown/bin/python"

# Cap CPU threads to reduce system-wide stutter during heavy BaB rounds.
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-4}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-4}"

mkdir -p "${LOG_DIR}" "${META_DIR}"

strategies=("baseline" "auto" "kfsb")
epsilons=("0.01" "0.02" "0.03" "0.05")

run_chunked_eps005() {
  local run_id="$1"
  local cfg_path="$2"
  local log_path="$3"
  local meta_path="$4"

  local chunk_dir="${LOG_DIR}/chunks/${run_id}"
  mkdir -p "${chunk_dir}"

  # Run 10 samples per process to avoid long single-process pressure on WSL.
  local start=0
  local chunk_size=10
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
      --batch_size 64 --timeout 12 \
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

  # Aggregate chunk summaries into one synthetic summary log for downstream parser.
  "${PYTHON_BIN}" - <<'PY' "${chunk_dir}" "${run_id}" "${log_path}"
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

if total == 0:
    out_log.write_text(f"[ERROR] No valid chunk summaries for {run_id}\n", encoding="utf-8")
    sys.exit(2)

final_acc = 100.0 * safe / total
mean_time = weighted_time / total

lines = [
    f"############# Summary #############",
    f"Final verified acc: {final_acc:.1f}% (total {total} examples)",
    f"Problem instances count: {total} , total verified (safe/unsat): {safe} , total falsified (unsafe/sat): {unsafe} , timeout: {timeout}",
    f"mean time for ALL instances (total {total}):{mean_time}, max time: {max_time}",
    "",
]
out_log.write_text("\n".join(lines), encoding="utf-8")
PY
}

run_chunked_kfsb_hard() {
  local run_id="$1"
  local cfg_path="$2"
  local log_path="$3"
  local meta_path="$4"
  local chunk_size="$5"
  local batch_size="$6"
  local timeout_sec="$7"
  local mip_proc="$8"
  local mip_refine_timeout="$9"

  local chunk_dir="${LOG_DIR}/chunks/${run_id}"
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
      --mip_multi_proc "${mip_proc}" --mip_threads 1 --mip_perneuron_refine_timeout "${mip_refine_timeout}" \
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

  "${PYTHON_BIN}" - <<'PY' "${chunk_dir}" "${run_id}" "${log_path}"
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

if total == 0:
    out_log.write_text(f"[ERROR] No valid chunk summaries for {run_id}\n", encoding="utf-8")
    sys.exit(2)

final_acc = 100.0 * safe / total
mean_time = weighted_time / total
out_log.write_text(
    "\n".join([
        "############# Summary #############",
        f"Final verified acc: {final_acc:.1f}% (total {total} examples)",
        f"Problem instances count: {total} , total verified (safe/unsat): {safe} , total falsified (unsafe/sat): {unsafe} , timeout: {timeout}",
        f"mean time for ALL instances (total {total}):{mean_time}, max time: {max_time}",
        "",
    ]),
    encoding="utf-8",
)
PY
}

cd "${CV_DIR}"

for s in "${strategies[@]}"; do
  for e in "${epsilons[@]}"; do
    run_id="${s}_eps${e}"
    cfg_path="${CFG_DIR}/mnist_m4_${s}_eps${e}.yaml"
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
      echo "gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1 || true)"
    } > "${meta_path}"

    echo "[RUN] ${run_id}"
    echo "threads: OMP=${OMP_NUM_THREADS}, MKL=${MKL_NUM_THREADS}, OPENBLAS=${OPENBLAS_NUM_THREADS}" >> "${meta_path}"

    if [[ "${s}" == "kfsb" && "${e}" == "0.03" ]]; then
      set +e
      run_chunked_kfsb_hard "${run_id}" "${cfg_path}" "${log_path}" "${meta_path}" 10 96 15 2 6
      rc=$?
      set -e
    elif [[ "${s}" == "kfsb" && "${e}" == "0.05" ]]; then
      set +e
      run_chunked_kfsb_hard "${run_id}" "${cfg_path}" "${log_path}" "${meta_path}" 10 64 12 2 5
      rc=$?
      set -e
    elif [[ "${e}" == "0.05" ]]; then
      set +e
      run_chunked_eps005 "${run_id}" "${cfg_path}" "${log_path}" "${meta_path}"
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
