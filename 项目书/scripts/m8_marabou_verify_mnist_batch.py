#!/usr/bin/env python3
"""
M8: 5-sample MNIST tool comparison (Marabou vs alpha-beta-CROWN).
Batch verification for samples 0–4, epsilon=0.01.

Outputs:
  - CSV: 项目书/results/m8_marabou/m8_marabou_5samples_eps0.01.csv
  - JSON: 项目书/results/m8_marabou/m8_marabou_5samples_eps0.01.json
"""

import sys, os, json, csv, time, argparse, warnings
warnings.filterwarnings("ignore")

BASE_DIR = "/home/han/alpha-beta-CROWN"
MODEL_PATH = os.path.join(BASE_DIR, "saved_models", "mnist_fcnn.onnx")
RESULTS_DIR = os.path.join(BASE_DIR, "项目书", "results", "m8_marabou")
sys.path.insert(0, os.path.join(BASE_DIR, "auto_LiRPA"))

import numpy as np
import torch
from torchvision import datasets, transforms
import onnxruntime as ort

# ─── Data loading ───────────────────────────────────────────────

def load_mnist():
    """Return list of (img_tensor, label) for test set."""
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    ds = datasets.MNIST(
        os.path.join(BASE_DIR, "data"),
        train=False, download=True,
        transform=transforms.ToTensor()
    )
    return [(ds[i][0], int(ds[i][1])) for i in range(len(ds))]

def get_logits(x_np):
    """Run ONNX Runtime inference, return logits numpy array (length 10)."""
    sess = ort.InferenceSession(MODEL_PATH)
    return sess.run(None, {"input": x_np[None, ...]})[0][0]

# ─── Marabou verification ──────────────────────────────────────

def verify_marabou(sample_idx, x_flat, true_label, eps, timeout):
    """
    Run Marabou complete verification on one sample.
    Returns dict: status, time, details.
    """
    from maraboupy import Marabou

    t_start = time.time()
    try:
        network = Marabou.read_onnx(MODEL_PATH)
    except Exception as e:
        return {"status": "ERROR", "time_s": round(time.time() - t_start, 3),
                "error": f"read_onnx: {e}"}

    output_vars = network.outputVars[0][0]  # shape (10,)
    pred_label = int(np.argmax(get_logits(x_flat.reshape(1, 28, 28))))

    targets = [j for j in range(10) if j != true_label]
    # Sort by predicted logit difference (hardest first)
    # Use a quick inference to sort
    logits_all = get_logits(x_flat.reshape(1, 28, 28))
    targets.sort(key=lambda j: logits_all[j] - logits_all[true_label], reverse=True)

    target_results = {}
    verdicts = []
    total_solve_time = 0.0

    for target_label in targets:
        # Fresh network per target
        try:
            net = Marabou.read_onnx(MODEL_PATH)
        except Exception:
            target_results[str(target_label)] = {"verdict": "ERROR", "time_s": 0}
            verdicts.append("ERROR")
            continue

        ov = net.outputVars[0][0]

        # Input bounds
        for i in range(784):
            lb = max(0.0, float(x_flat[i]) - eps)
            ub = min(1.0, float(x_flat[i]) + eps)
            net.setLowerBound(i, lb)
            net.setUpperBound(i, ub)

        # Constraint: output[target] >= output[true_label]
        # → output[true] - output[target] <= 0
        net.addInequality(
            [int(ov[true_label]), int(ov[target_label])],
            [1.0, -1.0],
            0.0
        )

        t1 = time.time()
        try:
            exitCode, vals, stats = net.solve(
                options=Marabou.createOptions(timeoutInSeconds=timeout, verbosity=0),
                verbose=False
            )
        except Exception as e:
            target_results[str(target_label)] = {"verdict": f"ERROR: {e}", "time_s": 0}
            verdicts.append("ERROR")
            continue

        elapsed = round(time.time() - t1, 3)
        total_solve_time += elapsed

        code_str = str(exitCode).strip().lower()
        if code_str == "sat":
            verdict = "SAT"
        elif code_str == "unsat":
            verdict = "UNSAT"
        elif "timeout" in code_str:
            verdict = "TIMEOUT"
        else:
            verdict = f"ERROR({code_str})"

        target_results[str(target_label)] = {"verdict": verdict, "time_s": elapsed}
        verdicts.append(verdict)

        if verdict == "SAT":
            break  # Early termination: sample is unsafe

    # Overall status
    if "SAT" in verdicts:
        overall = "unsafe"
    elif "TIMEOUT" in verdicts:
        overall = "unknown"
    elif "ERROR" in verdicts:
        overall = "error"
    elif all(v == "UNSAT" for v in verdicts):
        overall = "safe"
    else:
        overall = "error"

    return {
        "status": overall,
        "time_s": round(time.time() - t_start, 3),
        "solve_time_s": round(total_solve_time, 3),
        "targets_tested": len(verdicts),
        "target_results": target_results,
        "true_label": true_label,
        "pred_label": pred_label,
    }

# ─── alpha-beta-CROWN verification ─────────────────────────────

def verify_abcrown(sample_idx, x_flat, true_label, eps):
    """Run alpha-beta-CROWN incomplete verification on one sample."""
    from auto_LiRPA import BoundedModule, BoundedTensor
    from auto_LiRPA.perturbations import PerturbationLpNorm
    import onnx
    from onnx2pytorch import ConvertModel

    t_start = time.time()
    try:
        onnx_model = onnx.load(MODEL_PATH)
        pt_model = ConvertModel(onnx_model)
        pt_model.eval()
        x_tensor = torch.from_numpy(x_flat.reshape(1, 1, 28, 28))
        bounded = BoundedModule(pt_model, x_tensor, bound_opts={
            "relu": "same-slope",
            "optimize_bound_args": {
                "iteration": 20,
                "lr_alpha": 0.05,
                "lr_decay": 0.5,
            }
        })
    except Exception as e:
        return {"status": "ERROR", "time_s": round(time.time() - t_start, 3),
                "error": f"model load: {e}"}

    x_lb = torch.clamp(x_tensor - eps, 0.0, 1.0)
    x_ub = torch.clamp(x_tensor + eps, 0.0, 1.0)
    x_bounded = BoundedTensor(x_tensor, PerturbationLpNorm(
        norm=np.inf, eps=eps, x_L=x_lb, x_U=x_ub
    ))

    t1 = time.time()
    try:
        lb, ub = bounded.compute_bounds(x=(x_bounded,), method="alpha-CROWN")
    except Exception as e:
        return {"status": "ERROR", "time_s": round(time.time() - t_start, 3),
                "error": f"compute_bounds: {e}"}

    lb_np = lb.detach().cpu().numpy().flatten()
    ub_np = ub.detach().cpu().numpy().flatten()

    verified = True
    for j in range(10):
        if j == true_label:
            continue
        if ub_np[j] - lb_np[true_label] >= 0:
            verified = False
            break

    return {
        "status": "safe" if verified else "unknown",
        "time_s": round(time.time() - t_start, 3),
        "bound_time_s": round(time.time() - t1, 3),
        "lower_bounds": [float(v) for v in lb_np],
        "upper_bounds": [float(v) for v in ub_np],
        "true_label": true_label,
        "pred_label": int(np.argmax(get_logits(x_flat.reshape(1, 28, 28)))),
    }

# ─── Main ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=str, default="0,1,2,3,4")
    parser.add_argument("--epsilon", type=float, default=0.01)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    sample_indices = [int(s.strip()) for s in args.samples.split(",")]
    eps = args.epsilon
    timeout = args.timeout

    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("=" * 70)
    print(f"M8 5-Sample Tool Comparison")
    print(f"Samples: {sample_indices}, Epsilon: {eps}, Timeout: {timeout}s")
    print("=" * 70)

    data = load_mnist()
    rows = []

    for idx in sample_indices:
        print(f"\n{'─' * 50}")
        print(f"Sample {idx}")
        print(f"{'─' * 50}")

        x_tensor, true_label = data[idx]
        x_flat = x_tensor.numpy().flatten().astype(np.float32)
        logits = get_logits(x_flat.reshape(1, 28, 28))
        pred_label = int(np.argmax(logits))

        print(f"  True={true_label}, Pred={pred_label}, logits: {[f'{v:.2f}' for v in logits]}")

        # alpha-beta-CROWN
        print(f"  α,β-CROWN...", end=" ", flush=True)
        abc_result = verify_abcrown(idx, x_flat, true_label, eps)
        print(f"{abc_result['status']} ({abc_result['time_s']:.2f}s)")

        # Marabou
        print(f"  Marabou...", end=" ", flush=True)
        mar_result = verify_marabou(idx, x_flat, true_label, eps, timeout)
        print(f"{mar_result['status']} ({mar_result['time_s']:.2f}s)")

        # Consistency
        if mar_result["status"] == "safe" and abc_result["status"] == "safe":
            consistent = True
        elif mar_result["status"] == "unsafe" and abc_result["status"] == "unknown":
            consistent = "partial"  # Marabou found counterexample, CROWN couldn't prove safety
        elif mar_result["status"] == "unsafe" and abc_result["status"] == "safe":
            consistent = False  # Should not happen if CROWN is sound
        elif mar_result["status"] == "unknown" and abc_result["status"] == "unknown":
            consistent = True  # Both timed out
        elif mar_result["status"] == "error" or abc_result["status"] == "error":
            consistent = "error"
        else:
            consistent = None

        row = {
            "sample_idx": idx,
            "true_label": true_label,
            "pred_label": pred_label,
            "epsilon": eps,
            "marabou_status": mar_result["status"],
            "marabou_time_s": mar_result["time_s"],
            "abcrown_status": abc_result["status"],
            "abcrown_time_s": abc_result["time_s"],
            "result_consistent": consistent,
        }
        rows.append(row)

    # ─── Write CSV ──────────────────────────────────────────────
    csv_path = os.path.join(RESULTS_DIR, f"m8_marabou_5samples_eps{eps}.csv")
    fieldnames = [
        "sample_idx", "true_label", "pred_label", "epsilon",
        "marabou_status", "marabou_time_s",
        "abcrown_status", "abcrown_time_s",
        "result_consistent"
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nCSV: {csv_path}")

    # ─── Write JSON ──────────────────────────────────────────────
    json_path = os.path.join(RESULTS_DIR, f"m8_marabou_5samples_eps{eps}.json")
    with open(json_path, "w") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"JSON: {json_path}")

    # ─── Summary ─────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")

    n = len(rows)
    n_consistent = sum(1 for r in rows if r["result_consistent"] is True)
    mar_times = [r["marabou_time_s"] for r in rows if r["marabou_status"] not in ("error",)]
    abc_times = [r["abcrown_time_s"] for r in rows if r["abcrown_status"] not in ("error",)]
    mar_statuses = [r["marabou_status"] for r in rows]
    abc_statuses = [r["abcrown_status"] for r in rows]

    print(f"  Samples: {n}")
    print(f"  Consistent: {n_consistent}/{n}")
    print(f"  Marabou avg time: {np.mean(mar_times):.2f}s" if mar_times else "  Marabou: N/A")
    print(f"  α,β-CROWN avg time: {np.mean(abc_times):.2f}s" if abc_times else "  α,β-CROWN: N/A")
    print(f"  Marabou statuses: {dict((s, mar_statuses.count(s)) for s in set(mar_statuses))}")
    print(f"  α,β-CROWN statuses: {dict((s, abc_statuses.count(s)) for s in set(abc_statuses))}")

    return rows

if __name__ == "__main__":
    main()
