from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT_DIR = Path("/home/han/alpha-beta-CROWN")
CSV_PATH = ROOT_DIR / "项目书/results/m4/m4_epsilon_grid.csv"
FIG_DIR = ROOT_DIR / "项目书/results/m4/figures"

COLORS = {
    "baseline": "#4C78A8",
    "auto": "#F58518",
    "kfsb": "#54A24B",
}


def main():
    df = pd.read_csv(CSV_PATH)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(7, 4))
    for s in ["baseline", "auto", "kfsb"]:
        g = df[df["strategy"] == s].sort_values("epsilon")
        if g.empty:
            continue
        plt.plot(g["epsilon"], g["verified_acc"], marker="o", label=s, color=COLORS.get(s))
    plt.xlabel("epsilon")
    plt.ylabel("verified acc (%)")
    plt.title("M4 VRA-Epsilon")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "m4_vra_epsilon.png", dpi=180)
    plt.close()

    plt.figure(figsize=(7, 4))
    for s in ["baseline", "auto", "kfsb"]:
        g = df[df["strategy"] == s].sort_values("epsilon")
        if g.empty:
            continue
        plt.plot(g["epsilon"], g["mean_time_s"], marker="o", label=f"{s}-mean", color=COLORS.get(s))
    plt.xlabel("epsilon")
    plt.ylabel("mean time (s)")
    plt.title("M4 MeanTime-Epsilon")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "m4_mean_time_epsilon.png", dpi=180)
    plt.close()

    plt.figure(figsize=(7, 4))
    for s in ["baseline", "auto", "kfsb"]:
        g = df[df["strategy"] == s].sort_values("epsilon")
        if g.empty:
            continue
        plt.plot(g["epsilon"], g["timeout"], marker="o", label=s, color=COLORS.get(s))
    plt.xlabel("epsilon")
    plt.ylabel("timeout count")
    plt.title("M4 Timeout-Epsilon")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "m4_timeout_epsilon.png", dpi=180)
    plt.close()

    print(f"[OK] Figures saved in: {FIG_DIR}")


if __name__ == "__main__":
    main()
