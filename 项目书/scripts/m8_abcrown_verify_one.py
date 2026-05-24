#!/usr/bin/env python3
"""
M8 Stage 5: alpha-beta-CROWN single-sample verification (comparison).
Uses auto_LiRPA (the core of α,β-CROWN) directly.
Runs CROWN + α-CROWN incomplete verification on one MNIST sample.

Usage:
    python m8_abcrown_verify_one.py --sample_idx 0 --epsilon 0.01
"""

import sys, os, json, time, argparse, warnings
warnings.filterwarnings("ignore")

BASE_DIR = "/home/han/alpha-beta-CROWN"

# Add auto_LiRPA submodule to path (avoids pip install issues)
sys.path.insert(0, os.path.join(BASE_DIR, "auto_LiRPA"))

import numpy as np
import torch
from torchvision import datasets, transforms
import onnx
from onnx2pytorch import ConvertModel
MODEL_PATH = os.path.join(BASE_DIR, "saved_models", "mnist_fcnn.onnx")
RESULTS_DIR = os.path.join(BASE_DIR, "项目书", "results", "m8_marabou")

def load_model():
    """Load the MNIST FCNN model from ONNX and wrap in auto_LiRPA BoundedModule."""
    from auto_LiRPA import BoundedModule, BoundedTensor
    from auto_LiRPA.perturbations import PerturbationLpNorm

    # Convert ONNX → PyTorch
    onnx_model = onnx.load(MODEL_PATH)
    pytorch_model = ConvertModel(onnx_model)
    pytorch_model.eval()

    # Wrap in auto_LiRPA BoundedModule
    dummy_input = torch.randn(1, 1, 28, 28)
    bounded = BoundedModule(pytorch_model, dummy_input, bound_opts={
        "relu": "same-slope",
        "optimize_bound_args": {
            "iteration": 20,
            "lr_alpha": 0.05,
            "lr_decay": 0.5,
        }
    })
    return bounded

def load_sample(idx):
    """Return (img_tensor, label)."""
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    ds = datasets.MNIST(
        os.path.join(BASE_DIR, "data"),
        train=False, download=True,
        transform=transforms.ToTensor()
    )
    img, label = ds[idx]
    return img.unsqueeze(0), int(label)  # shape [1, 1, 28, 28]

def verify_crown(bounded, x, true_label, eps):
    """
    Run CROWN + α-CROWN bound propagation.
    Returns dict with per-class lower/upper bounds, and overall verdict.
    """
    from auto_LiRPA import BoundedTensor
    from auto_LiRPA.perturbations import PerturbationLpNorm

    x_lb = torch.clamp(x - eps, 0.0, 1.0)
    x_ub = torch.clamp(x + eps, 0.0, 1.0)
    x_bounded = BoundedTensor(x, PerturbationLpNorm(norm=np.inf, eps=eps, x_L=x_lb, x_U=x_ub))

    t0 = time.time()
    # α-CROWN: optimize bounds with gradient-based alpha tuning
    lb, ub = bounded.compute_bounds(x=(x_bounded,), method="alpha-CROWN")
    elapsed = time.time() - t0

    lb_np = lb.detach().cpu().numpy().flatten()
    ub_np = ub.detach().cpu().numpy().flatten()

    # Check safety: for all j != true_label, ub_j - lb_true < 0
    # (if output[target] can exceed output[true], the sample is UNKNOWN)
    verified = True
    for j in range(10):
        if j == true_label:
            continue
        if ub_np[j] - lb_np[true_label] >= 0:
            verified = False
            break

    verdict = "safe" if verified else "unknown"
    return {
        "verdict": verdict,
        "lower_bounds": [float(v) for v in lb_np],
        "upper_bounds": [float(v) for v in ub_np],
        "time_s": round(elapsed, 3),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample_idx", type=int, default=0)
    parser.add_argument("--epsilon", type=float, default=0.01)
    args = parser.parse_args()

    print(f"alpha-beta-CROWN single-sample verification")
    print(f"  Sample: {args.sample_idx}, Epsilon: {args.epsilon}")
    print()

    # Load data
    print("[1/3] Loading sample...")
    x, true_label = load_sample(args.sample_idx)
    print(f"  True label: {true_label}, shape: {x.shape}")

    # Run model prediction
    print("\n[2/3] Running model prediction...")
    with torch.no_grad():
        logits = bounded_model(x, method_opt="forward")
    pred = int(torch.argmax(logits))
    print(f"  Predicted: {pred}, logits: {[f'{v:.3f}' for v in logits.flatten()]}")

    # CROWN + α-CROWN verification
    print(f"\n[3/3] alpha-beta-CROWN verification...")
    result = verify_crown(bounded_model, x, true_label, args.epsilon)

    print(f"  Result: {result['verdict']}")
    print(f"  Time: {result['time_s']:.3f}s")
    for j in range(10):
        marker = "*" if j == true_label else " "
        print(f"  [{marker}] class {j}: [{result['lower_bounds'][j]:.4f}, {result['upper_bounds'][j]:.4f}]")

    # Determine if any target class could exceed true
    lb_true = result['lower_bounds'][true_label]
    worst_targets = []
    for j in range(10):
        if j == true_label:
            continue
        gap = result['upper_bounds'][j] - lb_true
        if gap >= 0:
            worst_targets.append({"target": j, "gap": round(gap, 4)})
    worst_targets.sort(key=lambda x: x["gap"], reverse=True)

    print(f"\n  Classes that could exceed true label {true_label}: {worst_targets}")

    # Save JSON
    output = {
        "tool": "alpha-beta-CROWN",
        "method": "CROWN + alpha-CROWN (incomplete)",
        "sample_idx": args.sample_idx,
        "epsilon": args.epsilon,
        "true_label": true_label,
        "pred_label": pred,
        "logits": [float(v) for v in logits.flatten()],
        "overall_result": result['verdict'],
        "lower_bounds": result['lower_bounds'],
        "upper_bounds": result['upper_bounds'],
        "time_s": result['time_s'],
        "worst_targets": worst_targets,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    json_path = os.path.join(RESULTS_DIR, "m8_abcrown_one_sample.json")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n  JSON: {json_path}")

    return result['verdict'], output

if __name__ == "__main__":
    # Global model load (reusable)
    print("[0/3] Loading model and wrapping in auto_LiRPA...")
    bounded_model = load_model()
    print("  Model loaded OK\n")

    verdict, _ = main()
    print(f"\nFinal result: {verdict}")
