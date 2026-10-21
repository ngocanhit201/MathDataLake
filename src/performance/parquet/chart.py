import csv
import math
from pathlib import Path
from statistics import median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter


CONFIGURATIONS = ("parquet_4", "parquet_8", "parquet_16")
METRICS = {
    "elapsed_seconds": ("Thời gian đọc và giải mã Parquet", "Thời gian (giây)", "Thấp hơn là tốt hơn"),
    "mb_per_second": ("Tốc độ đọc Parquet theo dung lượng", "Tốc độ (MB/giây)", "Cao hơn là tốt hơn"),
    "rows_per_second": ("Tốc độ đọc Parquet theo bản ghi", "Tốc độ (bản ghi/giây)", "Cao hơn là tốt hơn"),
}


# Đọc CSV, loại lượt lỗi hoặc thiếu số đo và nhóm theo cấu hình 4, 8, 16 file.
def read_results(path: Path) -> dict:
    groups = {name: [] for name in CONFIGURATIONS}
    skipped = 0
    with path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        required = {"configuration", "run", "files_error", *METRICS}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("CSV thiếu cột cấu hình, lượt chạy, lỗi file hoặc chỉ số hiệu năng")
        for row in reader:
            if row["configuration"] not in groups:
                raise ValueError(f"Cấu hình không hỗ trợ: {row['configuration']}")
            if int(row["files_error"]) > 0 or any(not row[key] for key in METRICS):
                skipped += 1
                continue
            values = {key: float(row[key]) for key in METRICS}
            if any(not math.isfinite(value) or value <= 0 for value in values.values()):
                skipped += 1
                continue
            values["run"] = int(row["run"])
            records = groups[row["configuration"]]
            if any(record["run"] == values["run"] for record in records):
                raise ValueError(f"Trùng lượt {values['run']}: {row['configuration']}")
            records.append(values)
    missing = [name for name, records in groups.items() if not records]
    if missing:
        raise ValueError(f"Không có số đo hợp lệ: {', '.join(missing)}")
    if skipped:
        print(f"Đã loại {skipped} lượt lỗi hoặc thiếu số đo.")
    return groups


# Vẽ cột trung vị và các điểm từng lượt trên trục Y tuyến tính bắt đầu từ 0.
def save_chart(groups: dict, metric: str, output_dir: Path) -> Path:
    title, ylabel, direction = METRICS[metric]
    values = [[row[metric] for row in groups[name]] for name in CONFIGURATIONS]
    medians = [median(items) for items in values]
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.bar(range(3), medians, width=0.58, color="#87b8cc", label="Trung vị", zorder=2)
    for index, items in enumerate(values):
        positions = [index + (offset / (len(items) - 1) - 0.5) * 0.28
                     if len(items) > 1 else index for offset in range(len(items))]
        ax.scatter(positions, items, color="#16364a", s=35, zorder=3,
                   label="Từng lượt đo" if index == 0 else None)
        ax.annotate(f"{medians[index]:,.2f}", (index, max(items)), xytext=(0, 9),
                    textcoords="offset points", ha="center", weight="bold")
    ax.set_title(f"{title} (PyArrow)", fontsize=14, weight="bold", pad=16)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Cấu hình lưu trữ")
    ax.set_xticks(range(3), [f"{name.split('_')[1]} file\nn = {len(groups[name])}"
                            for name in CONFIGURATIONS])
    ax.set_ylim(0, max(max(items) for items in values) * 1.24)
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}" if metric == "rows_per_second" else "{x:g}"))
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper right", frameon=False)
    note = "Có cấu hình chỉ có 1 lượt đo; chưa đủ kết luận về hiệu năng." if any(
        len(items) == 1 for items in values) else "Các điểm thể hiện độ phân tán giữa các lượt đo."
    fig.text(0.5, 0.055, f"{direction} · 1 MB = 1.000.000 bytes", ha="center", fontsize=9)
    fig.text(0.5, 0.02, note, ha="center", fontsize=9, color="#555555")
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{metric}.png"
    fig.savefig(path, dpi=300, facecolor="white")
    plt.close(fig)
    return path


# Tạo ba biểu đồ từ CSV hiện có, không chạy lại phép đo hiệu năng.
def create_charts() -> list[Path]:
    output_dir = Path(__file__).resolve().parents[3] / "results/performance/parquet"
    groups = read_results(output_dir / "data.csv")
    return [save_chart(groups, metric, output_dir) for metric in METRICS]


if __name__ == "__main__":
    for path in create_charts():
        print(path)
