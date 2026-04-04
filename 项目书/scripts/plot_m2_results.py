from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

ROOT_DIR = Path("/home/han/alpha-beta-CROWN")
CSV_PATH = ROOT_DIR / "项目书/results/m2/m2_strategy_compare_0_100.csv"
FIG_DIR = ROOT_DIR / "项目书/results/m2/figures"


def main():
    df = pd.read_csv(CSV_PATH)
    order = ["baseline", "auto", "kfsb"]
    df["run_id"] = pd.Categorical(df["run_id"], categories=order, ordered=True)
    df = df.sort_values("run_id")

    labels = df["run_id"].tolist()
    vra = df["verified_acc"].tolist()
    mean_time = df["mean_time_s"].tolist()
    max_time = df["max_time_s"].tolist()
    timeout = df["timeout"].tolist()

    colors = ["#4C78A8", "#F58518", "#54A24B"]
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(7, 4))
    bars = plt.bar(labels, mean_time, color=colors)
    for i, bar in enumerate(bars):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                 f"{mean_time[i]:.2f}s", ha="center", va="bottom", fontsize=9)
    plt.title("M2 Mean Time (MNIST 0-100, epsilon=0.02)")
    plt.ylabel("Seconds")
    plt.xlabel("Strategy")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "m2_mean_time.png", dpi=180)
    plt.close()

    plt.figure(figsize=(7, 4))
    bars = plt.bar(labels, max_time, color=colors)
    for i, bar in enumerate(bars):
        text = f"max={max_time[i]:.2f}s\\nVRA={vra[i]:.1f}%\\ntimeout={timeout[i]}"
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                 text, ha="center", va="bottom", fontsize=8)
    plt.title("M2 Max Time / VRA / Timeout")
    plt.ylabel("Seconds")
    plt.xlabel("Strategy")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "m2_max_time_vra_timeout.png", dpi=180)
    plt.close()

    print(f"[OK] Figures saved in: {FIG_DIR}")


if __name__ == "__main__":
    main()
