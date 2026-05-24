#!/usr/bin/env python3
"""
M8 Stage 4: Single-sample MNIST verification with Marabou.
Verify one MNIST sample at a given epsilon, using Marabou's SMT solver.

Outputs:
  - Console + log file: per-target results
  - JSON: summary saved to 项目书/results/m8_marabou/m8_marabou_one_sample.json
"""

import sys, os, json, time, argparse, warnings
warnings.filterwarnings("ignore")

import numpy as np
import torch
from torchvision import datasets, transforms
import onnxruntime as ort

BASE_DIR = "/home/han/alpha-beta-CROWN"
MODEL_PATH = os.path.join(BASE_DIR, "saved_models", "mnist_fcnn.onnx")
RESULTS_DIR = os.path.join(BASE_DIR, "项目书", "results", "m8_marabou")
LOG_DIR = os.path.join(RESULTS_DIR, "logs")

_log_fh = None

def tee(msg):
    print(msg)
    if _log_fh:
        _log_fh.write(msg + "\n")
        _log_fh.flush()

def load_mnist_sample(idx: int):
    """Return (img_np, label) where img_np shape = (1,28,28), dtype=float32."""
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    ds = datasets.MNIST(
        os.path.join(BASE_DIR, "data"),
        train=False, download=True,
        transform=transforms.ToTensor()
    )
    img, label = ds[idx]
    return img.numpy().astype(np.float32), int(label)

def verify_one_target(network, true_var, target_var, x0_flat, eps, timeout):
    """
    Check: exists x' s.t. |x'-x0|_inf ≤ eps, x'∈[0,1], f_target(x') ≥ f_true(x').
    Returns (verdict, elapsed_sec).
    """
    from maraboupy import Marabou

    # Input bounds
    for i in range(784):
        lb = max(0.0, float(x0_flat[i]) - eps)
        ub = min(1.0, float(x0_flat[i]) + eps)
        network.setLowerBound(i, lb)
        network.setUpperBound(i, ub)

    # Constraint: output[target] >= output[true]
    #   →  output[true] - output[target] <= 0
    network.addInequality(
        [int(true_var), int(target_var)],
        [1.0, -1.0],
        0.0
    )

    t0 = time.time()
    exitCode, vals, stats = network.solve(
        options=Marabou.createOptions(timeoutInSeconds=timeout, verbosity=0),
        verbose=False
    )
    elapsed = time.time() - t0

    code_str = str(exitCode).strip().lower()
    # Must compare exact string — "sat" vs "unsat"
    if code_str == "sat":
        verdict = "SAT"
    elif code_str == "unsat":
        verdict = "UNSAT"
    elif "timeout" in code_str:
        verdict = "TIMEOUT"
    else:
        verdict = f"ERROR({code_str})"

    return verdict, elapsed

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample_idx", type=int, default=0)
    parser.add_argument("--epsilon", type=float, default=0.01)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"one_sample_eps{args.epsilon}_wsl.log")
    global _log_fh
    _log_fh = open(log_path, "w")

    tee("=" * 60)
    tee(f"Marabou MNIST Single-Sample Verification")
    tee(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    tee(f"Sample: {args.sample_idx}  |  Epsilon: {args.epsilon}  |  Timeout: {args.timeout}s")
    tee("=" * 60)

    # ---- 1. Load MNIST sample ----
    tee("\n[1/5] Loading MNIST sample...")
    x0, true_label = load_mnist_sample(args.sample_idx)
    x0_flat = x0.flatten()
    tee(f"  True label: {true_label},  shape: {x0.shape},  range: [{x0_flat.min():.3f}, {x0_flat.max():.3f}]")

    # ---- 2. ONNX Runtime inference ----
    tee("\n[2/5] ONNX Runtime inference...")
    sess = ort.InferenceSession(MODEL_PATH)
    logits = sess.run(None, {"input": x0[None, ...]})[0][0]
    pred_label = int(np.argmax(logits))
    tee(f"  Predicted: {pred_label},  logits: {[f'{v:.3f}' for v in logits]}")

    # ---- 3. Load Marabou network ----
    tee("\n[3/5] Loading Marabou ONNX network...")
    from maraboupy import Marabou
    t0 = time.time()
    network0 = Marabou.read_onnx(MODEL_PATH)
    tee(f"  Loaded in {time.time()-t0:.2f}s")

    # Variable extraction: inputVars[0] shape (1,1,28,28); outputVars[0] shape (1,10)
    # inputVars[0][0].flatten() → 784 IDs (0–783); outputVars[0][0] → 10 IDs
    input_ids = network0.inputVars[0][0].flatten()   # np array, 784 elements
    output_ids = network0.outputVars[0][0]            # np array, 10 elements
    tee(f"  Input vars: {len(input_ids)} (IDs {input_ids[0]}–{input_ids[-1]})")
    tee(f"  Output vars: {len(output_ids)} (IDs {output_ids[0]}–{output_ids[-1]})")

    # ---- 4. Per-target verification ----
    tee("\n[4/5] Verifying against each target label...")

    targets = [j for j in range(10) if j != pred_label]
    # Sort by how close the logit is → harder targets first
    targets.sort(key=lambda j: logits[j] - logits[pred_label], reverse=True)

    results = {}
    verdicts = []
    total_time = 0.0

    for target_label in targets:
        diff = logits[target_label] - logits[pred_label]
        tee(f"\n  --- Target {target_label} (logit={logits[target_label]:.3f}, diff={diff:+.3f}) ---")

        # Fresh network per target (constraints are additive)
        network = Marabou.read_onnx(MODEL_PATH)

        verdict, elapsed = verify_one_target(
            network,
            output_ids[pred_label],
            output_ids[target_label],
            x0_flat, args.epsilon, args.timeout
        )
        total_time += elapsed

        results[str(target_label)] = {
            "verdict": verdict,
            "time_s": round(elapsed, 3)
        }
        verdicts.append(verdict)

        tee(f"    Result: {verdict} ({elapsed:.3f}s)")

        if verdict == "SAT":
            tee(f"\n  >>> SAT for target {target_label} → sample is UNSAFE (stopping).")
            break

    # ---- 5. Summary ----
    tee("\n[5/5] Final summary")

    if "SAT" in verdicts:
        overall = "unsafe"
        why = f"Counterexample found for target(s): {[k for k,v in results.items() if v['verdict']=='SAT']}"
    elif "TIMEOUT" in verdicts:
        overall = "unknown"
        why = f"Timeout on {verdicts.count('TIMEOUT')}/{len(verdicts)} target(s)"
    elif all(v == "UNSAT" for v in verdicts):
        overall = "safe"
        why = "No counterexample exists for any target label"
    else:
        overall = "error"
        why = f"Unexpected results: {verdicts}"

    tee(f"  Overall: {overall} — {why}")
    tee(f"  Total solve time: {total_time:.3f}s  |  Targets tested: {len(verdicts)}")

    output = {
        "tool": "Marabou",
        "sample_idx": args.sample_idx,
        "epsilon": args.epsilon,
        "timeout_per_target": args.timeout,
        "true_label": true_label,
        "pred_label": pred_label,
        "logits": [float(v) for v in logits],
        "overall_result": overall,
        "overall_explanation": why,
        "total_time_s": round(total_time, 3),
        "targets_tested": len(verdicts),
        "target_results": results,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    json_path = os.path.join(RESULTS_DIR, "m8_marabou_one_sample.json")
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    tee(f"\n  JSON: {json_path}")

    tee("\n" + "=" * 60)
    tee(f"Verification complete: {overall}")
    tee("=" * 60)

    _log_fh.close()
    return overall, output

if __name__ == "__main__":
    result, _ = main()
    print(f"\nFinal result: {result}")
