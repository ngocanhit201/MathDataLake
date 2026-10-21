import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

METRICS = {
    "elapsed_seconds": ("Thời gian đọc và parse JSONL", "Thời gian (giây)", True),
    "mb_per_second": ("Tốc độ đọc và parse theo dung lượng", "Tốc độ (MB/giây)", False),
    "rows_per_second": ("Tốc độ đọc và parse theo bản ghi", "Tốc độ (bản ghi/giây)", False),
}
LABELS = {"proofNet": "ProofNet", "numinaMath": "NuminaMath", "leanDojo": "LeanDojo"}


# Đọc số đo từng lượt từ CSV và nhóm theo dataset.
def read_results(path: Path) -> dict:
    groups = defaultdict(list)
    with path.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            record = {metric: float(row[metric]) for metric in METRICS}
            record["run"] = int(row["run"])
            if any(not math.isfinite(value) or value <= 0 for value in record.values()):
                raise ValueError(f"Số đo phải hữu hạn và lớn hơn 0: {row['dataset']}")
            groups[row["dataset"]].append(record)
    if not groups:
        raise ValueError("CSV không có số đo")
    return dict(groups)


# Vẽ mỗi lượt thành một cột riêng, có màu và nhãn số đo tương ứng.
def draw_measurements(ax, groups: dict, metric: str, logarithmic: bool) -> None:
    runs = sorted({row["run"] for records in groups.values() for row in records})
    values = [row[metric] for records in groups.values() for row in records]
    bottom = min(values) / 3 if logarithmic else 0
    width = 0.78 / len(runs)
    colors = ("#407da6", "#e3a34c", "#63a893")
    for run_index, run in enumerate(runs):
        for dataset_index, records in enumerate(groups.values()):
            matches = [row[metric] for row in records if row["run"] == run]
            if len(matches) != 1:
                raise ValueError(f"Mỗi dataset phải có đúng một số đo cho lượt {run}")
            value = matches[0]
            x = dataset_index + (run_index - (len(runs) - 1) / 2) * width
            ax.bar(x, value - bottom, bottom=bottom, width=width * 0.9,
                   color=colors[run_index % len(colors)], zorder=2,
                   label=f"Lượt {run}" if dataset_index == 0 else None)
            label = f"{value:.4f}" if value < 0.01 else f"{value:,.2f}"
            ax.annotate(label, (x, value), xytext=(0, 6), textcoords="offset points",
                        ha="center", fontsize=9, weight="bold")
    if logarithmic:
        ax.set_yscale("log")
        ax.set_ylim(bottom, max(values) * 3)
    else:
        ax.set_ylim(0, max(values) * 1.2)


# Định dạng tiêu đề, trục, chú thích và xuất một biểu đồ PNG 300 DPI.
def save_chart(groups: dict, metric: str, output_dir: Path) -> Path:
    title, ylabel, logarithmic = METRICS[metric]
    fig, ax = plt.subplots(figsize=(12, 6))
    draw_measurements(ax, groups, metric, logarithmic)
    ax.set_title(title, fontsize=15, weight="bold", pad=16)
    ax.set_ylabel(ylabel)
    ax.set_xticks(range(len(groups)), [LABELS.get(name, name) for name in groups])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, position: f"{value:g}"))
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.13), ncol=3, frameon=False)
    note = "Trục Y logarithm" if logarithmic else "Trục Y tuyến tính"
    fig.text(0.98, 0.025, f"{note} · 1 MB = 1.000.000 bytes", ha="right", fontsize=9, color="#555555")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    path = output_dir / f"{metric}.png"
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)
    return path


# Tạo ba biểu đồ từ số đo hiện có, không chạy lại benchmark.
def create_charts() -> list[Path]:
    root = Path(__file__).resolve().parents[3]
    output_dir = root / "results/performance/jsonl"
    groups = read_results(output_dir / "data.csv")
    output_dir.mkdir(parents=True, exist_ok=True)
    return [save_chart(groups, metric, output_dir) for metric in METRICS]


if __name__ == "__main__":
    for path in create_charts():
        print(path)
