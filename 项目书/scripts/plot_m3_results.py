from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT_DIR = Path("/home/han/alpha-beta-CROWN")
CSV_PATH = ROOT_DIR / "项目书/results/m3/m3_branching_ablation.csv"
FIG_DIR = ROOT_DIR / "项目书/results/m3/figures"

LABELS = [
    "baseline",
    "auto",
    "kfsb",
    "kfsb_reduceop_max",
    "kfsb_candidates5",
]

DISPLAY_NAMES = {
    "baseline": "baseline",
    "auto": "auto",
    "kfsb": "kfsb",
    "kfsb_reduceop_max": "kfsb + max",
    "kfsb_candidates5": "kfsb + c5",
}

COLORS = ["#4C78A8", "#F58518", "#54A24B", "#B279A2", "#E45756"]


def main():
    df = pd.read_csv(CSV_PATH)
    df["run_id"] = pd.Categorical(df["run_id"], categories=LABELS, ordered=True)
    df = df.sort_values("run_id")
    df["display_name"] = df["run_id"].map(DISPLAY_NAMES)

    FIG_DIR.mkdir(parents=True, exist_ok=True)

    x = range(len(df))

    plt.figure(figsize=(8, 4))
    plt.bar(x, df["verified_acc"], color=COLORS[: len(df)])
    plt.xticks(list(x), df["display_name"], rotation=20)
    plt.ylabel("verified acc (%)")
    plt.title("M3 Verified Accuracy")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "m3_verified_acc.png", dpi=180)
    plt.close()

    plt.figure(figsize=(8, 4))
    plt.bar(x, df["mean_time_s"], color=COLORS[: len(df)])
    plt.xticks(list(x), df["display_name"], rotation=20)
    plt.ylabel("mean time (sec)")
    plt.title("M3 Mean Time")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "m3_mean_time.png", dpi=180)
    plt.close()

    plt.figure(figsize=(8, 4))
    plt.bar(x, df["timeout"], color=COLORS[: len(df)])
    plt.xticks(list(x), df["display_name"], rotation=20)
    plt.ylabel("timeout count")
    plt.title("M3 Timeout Count")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "m3_timeout.png", dpi=180)
    plt.close()

    print(f"[OK] Figures saved in: {FIG_DIR}")


if __name__ == "__main__":
    main()
