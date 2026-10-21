import json
from pathlib import Path
import pyarrow.parquet as pq

root = Path(__file__).resolve().parents[1] / "results" / "parquet_8"
files = sorted((root / "data").glob("part-*.parquet"))
report = json.loads((root / "error.json").read_text(encoding="utf-8"))

# Kiểm tra số file, dung lượng và số bản ghi.
assert files, "Không tìm thấy file Parquet"
total = 0
schema = pq.ParquetFile(files[0]).schema_arrow

for path in files:
    parquet = pq.ParquetFile(path)
    assert parquet.schema_arrow.equals(schema), f"Schema khác: {path.name}"
    rows = parquet.metadata.num_rows
    total += rows
    size = path.stat().st_size / 1024**2
    print(f"{path.name}: {rows:,} dòng | {size:.2f} MiB")

# Đối chiếu dữ liệu đã ghi với báo cáo.
assert total == report["saved_records"], "Số dòng không khớp báo cáo"
assert report["total_records"] == total + report["rejected_records"]

print(f"\nTổng số dòng: {total:,}")
print(f"Tỷ lệ lỗi ETL: {report['error_rate']:.2%}")
print("\nSchema:")
print(schema)

# Đọc thử 3 bản ghi từ file đầu tiên.
parquet = pq.ParquetFile(files[0])
batch = next(parquet.iter_batches(
    batch_size=3,
    columns=["id", "dataset", "split", "content"]
))

print("\nBản ghi mẫu:")
for row in batch.to_pylist():
    content = row["content"]
    text = content["statement_text"] or content["lean_code"] or ""
    print(json.dumps({
        "id": row["id"],
        "dataset": row["dataset"],
        "split": row["split"],
        "noi_dung_300_ky_tu_dau": text[:300]
    }, ensure_ascii=False, indent=2))

print("\nKiểm tra hoàn tất.")
