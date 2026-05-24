#!/usr/bin/env python3
"""
M8 Stage 3: Marabou ONNX Read Test
Check if Marabou can parse the MNIST FCNN ONNX model.
No verification — just load and inspect.
"""

import sys
import os
import time

MODEL_PATH = "/home/han/alpha-beta-CROWN/saved_models/mnist_fcnn.onnx"
LOG_PATH = "/home/han/alpha-beta-CROWN/项目书/results/m8_marabou/logs/check_onnx_wsl.log"

def main():
    with open(LOG_PATH, "w") as log:
        def tee(msg):
            print(msg)
            log.write(msg + "\n")

        tee(f"Marabou ONNX Read Test — {time.strftime('%Y-%m-%d %H:%M:%S')}")
        tee(f"Model: {MODEL_PATH}")
        tee(f"Model exists: {os.path.exists(MODEL_PATH)}")
        tee(f"Model size: {os.path.getsize(MODEL_PATH)} bytes")
        tee("")

        # Step 1: Import Marabou
        tee("Step 1: Import maraboupy...")
        try:
            from maraboupy import Marabou
            from maraboupy import MarabouCore
            tee(f"  maraboupy imported OK")
        except Exception as e:
            tee(f"  FAILED: {e}")
            sys.exit(1)

        # Step 2: Load ONNX model
        tee("\nStep 2: Load ONNX model via Marabou.read_onnx()...")
        t0 = time.time()
        try:
            network = Marabou.read_onnx(MODEL_PATH)
            elapsed = time.time() - t0
            tee(f"  Loaded OK in {elapsed:.2f}s")
        except Exception as e:
            tee(f"  FAILED: {e}")
            sys.exit(1)

        # Step 3: Inspect network
        tee("\nStep 3: Inspect network structure...")
        try:
            input_vars = network.inputVars
            output_vars = network.outputVars
            tee(f"  Input variables ({len(input_vars)}):")
            for i, v in enumerate(input_vars):
                tee(f"    [{i}] shape={list(v[0].shape) if hasattr(v[0], 'shape') else 'flat'}, size={len(v)}")
            tee(f"  Output variables ({len(output_vars)}):")
            for i, v in enumerate(output_vars):
                tee(f"    [{i}] size={len(v)}")

            # Try to get more info
            nn = input_vars[0][0] if input_vars else None
            if nn is not None:
                tee(f"  Input variable detail: {nn}")
            oo = output_vars[0][0] if output_vars else None
            if oo is not None:
                tee(f"  Output variable detail: {oo}")

            tee(f"\n  Total input vars: {sum(len(v) for v in input_vars)}")
            tee(f"  Total output vars: {sum(len(v) for v in output_vars)}")

        except Exception as e:
            tee(f"  FAILED: {e}")
            sys.exit(1)

        # Step 4: Try to get equation count
        tee("\nStep 4: Check equation count...")
        try:
            n_equations = network.getNumberOfEquations()
            tee(f"  Equations: {n_equations}")
        except Exception as e:
            tee(f"  Could not get equation count: {e}")

        tee("\n" + "=" * 50)
        tee("ONNX Read Test: PASSED")
        tee("Marabou successfully parsed the MNIST FCNN ONNX model.")
        tee("=" * 50)

    print(f"\nLog written to: {LOG_PATH}")

if __name__ == "__main__":
    main()
