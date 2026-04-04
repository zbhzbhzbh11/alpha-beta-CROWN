import csv
import sys
from pathlib import Path
import matplotlib.pyplot as plt

csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('项目书/实验日志/2026-03-14_mnist_strategy_compare_0_20.csv')
fig_dir = Path('项目书/实验日志/figs')
fig_dir.mkdir(parents=True, exist_ok=True)

with csv_path.open('r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

labels = [r['run_id'] for r in rows]
mean_times = [float(r['mean_time_s']) for r in rows]
max_times = [float(r['max_time_s']) for r in rows]
accs = [float(r['verified_acc']) for r in rows]

plt.style.use('seaborn-v0_8-whitegrid')
colors = ['#2A9D8F', '#E9C46A', '#E76F51']

plt.figure(figsize=(7, 4))
plt.bar(labels, mean_times, color=colors)
for i, v in enumerate(mean_times):
    plt.text(i, v + 0.002, f'{v:.4f}s', ha='center', va='bottom', fontsize=9)
plt.title('MNIST(0-20) Mean Time Comparison')
plt.ylabel('Seconds')
plt.xlabel('Strategy')
plt.tight_layout()
mean_fig = fig_dir / f'{csv_path.stem}_mean_time_compare.png'
plt.savefig(mean_fig, dpi=180)
plt.close()

plt.figure(figsize=(7, 4))
plt.bar(labels, max_times, color=colors)
for i, (v, a) in enumerate(zip(max_times, accs)):
    plt.text(i, v + 0.01, f'max={v:.3f}s\nacc={a:.1f}%', ha='center', va='bottom', fontsize=9)
plt.title('MNIST(0-20) Max Time and Verified Acc')
plt.ylabel('Seconds')
plt.xlabel('Strategy')
plt.tight_layout()
max_fig = fig_dir / f'{csv_path.stem}_max_time_and_acc.png'
plt.savefig(max_fig, dpi=180)
plt.close()

print(mean_fig)
print(max_fig)
