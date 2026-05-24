#!/usr/bin/env python3
"""
M8 CIFAR-10 Marabou smoke test.
Single-target verification on 5 CIFAR-10 samples at epsilon=2/255.
Purpose: feasibility check — can Marabou handle CIFAR-10 ConvSmall?

Usage:
    python m8_marabou_cifar10_smoke.py --samples 0,1,2,3,4 --epsilon 0.007843 --timeout 120
"""

import sys, os, json, time, argparse, warnings
warnings.filterwarnings("ignore")

BASE_DIR = "/home/han/alpha-beta-CROWN"
MODEL_PATH = os.path.join(BASE_DIR, "saved_models", "cifar_marabou_small.onnx")
RESULTS_DIR = os.path.join(BASE_DIR, "项目书", "results", "m8_marabou")

import numpy as np
import torch
from torchvision import datasets, transforms
import onnxruntime as ort


def load_cifar10_test():
    """Return CIFAR-10 test set as list of (img_tensor, label). No normalization — raw [0,1]."""
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    ds = datasets.CIFAR10(
        os.path.join(BASE_DIR, "data"),
        train=False, download=True,
        transform=transforms.ToTensor()  # [0,1] range, no normalization
    )
    return [(ds[i][0], int(ds[i][1])) for i in range(len(ds))]


def get_logits(x_input):
    """ONNX Runtime inference. x_input: torch tensor shape (1, 3, 32, 32) or numpy."""
    sess = ort.InferenceSession(MODEL_PATH)
    if hasattr(x_input, 'numpy'):
        x_input = x_input.numpy().astype(np.float32)
    return sess.run(None, {"input": x_input})[0][0]  # shape (10,)


def run_marabou_target(x_flat, true_label, target_label, eps, timeout):
    """Run Marabou on one target. x_flat shape: (3072,)."""
    from maraboupy import Marabou

    t0 = time.time()
    try:
        network = Marabou.read_onnx(MODEL_PATH)
    except Exception as e:
        return {"verdict": f"ERROR:read_onnx:{e}", "time_s": round(time.time() - t0, 3)}

    output_vars = network.outputVars[0][0]  # shape (10,)
    N = len(x_flat)  # 3072

    # Set input bounds: clip to [0, 1]
    for i in range(N):
        lb = max(0.0, float(x_flat[i]) - eps)
        ub = min(1.0, float(x_flat[i]) + eps)
        network.setLowerBound(i, lb)
        network.setUpperBound(i, ub)

    # Constraint: output[target] >= output[true]
    network.addInequality(
        [int(output_vars[true_label]), int(output_vars[target_label])],
        [1.0, -1.0],
        0.0
    )

    t1 = time.time()
    try:
        exitCode, vals, stats = network.solve(
            options=Marabou.createOptions(timeoutInSeconds=timeout, verbosity=0),
            verbose=False
        )
    except Exception as e:
        return {"verdict": f"ERROR:solve:{e}", "time_s": round(time.time() - t0, 3)}

    elapsed = round(time.time() - t1, 3)

    code_str = str(exitCode).strip().lower()
    if code_str == "sat":
        verdict = "SAT"
    elif code_str == "unsat":
        verdict = "UNSAT"
    elif "timeout" in code_str:
        verdict = "TIMEOUT"
    else:
        verdict = f"OTHER({code_str})"

    return {"verdict": verdict, "time_s": elapsed, "total_s": round(time.time() - t0, 3)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=str, default="0,1,2,3,4")
    parser.add_argument("--epsilon", type=float, default=2.0/255.0)  # 0.007843...
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    sample_indices = [int(s.strip()) for s in args.samples.split(",")]
    eps = args.epsilon
    timeout = args.timeout

    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("=" * 60)
    print(f"CIFAR-10 Marabou Smoke Test")
    print(f"Samples: {sample_indices}, Epsilon: {eps:.6f} (2/255), Timeout: {timeout}s")
    print("=" * 60)

    data = load_cifar10_test()
    rows = []

    for idx in sample_indices:
        print(f"\n--- Sample {idx} ---")
        x_tensor, true_label = data[idx]
        x_flat = x_tensor.numpy().flatten().astype(np.float32)
        logits = get_logits(x_tensor.unsqueeze(0))
        pred_label = int(np.argmax(logits))

        print(f"  True={true_label}, Pred={pred_label}")
        print(f"  Logits: {dict((j, round(float(logits[j]),2)) for j in range(10))}")

        # Find hardest target (closest logit to true)
        targets = [(j, logits[j]) for j in range(10) if j != true_label]
        targets.sort(key=lambda t: t[1] - logits[true_label], reverse=True)
        hardest_target = targets[0][0]
        hardest_gap = round(float(targets[0][1] - logits[true_label]), 3)
        print(f"  Hardest target: {hardest_target} (gap={hardest_gap})")

        result = run_marabou_target(x_flat, true_label, hardest_target, eps, timeout)
        print(f"  Marabou: {result['verdict']} ({result['time_s']:.2f}s solve, {result.get('total_s', result['time_s']):.2f}s total)")

        rows.append({
            "sample_idx": idx,
            "true_label": true_label,
            "pred_label": pred_label,
            "target_tested": int(hardest_target),
            "target_logit_gap": hardest_gap,
            "epsilon": round(eps, 6),
            "timeout": timeout,
            "marabou_verdict": result["verdict"],
            "marabou_time_s": result["time_s"],
            "marabou_total_s": result.get("total_s", result["time_s"]),
        })

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    verdicts = [r["marabou_verdict"] for r in rows]
    times = [r["marabou_time_s"] for r in rows if not r["marabou_verdict"].startswith("ERROR")]
    print(f"  Verdicts: {dict((v, verdicts.count(v)) for v in set(verdicts))}")
    if times:
        print(f"  Avg solve time: {np.mean(times):.2f}s (n={len(times)})")
    print(f"  Total: {len(rows)} samples × 1 target each")

    # Save JSON
    json_path = os.path.join(RESULTS_DIR, "m8_marabou_cifar10_smoke.json")
    with open(json_path, "w") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"\n  JSON: {json_path}")

    return rows


if __name__ == "__main__":
    main()
