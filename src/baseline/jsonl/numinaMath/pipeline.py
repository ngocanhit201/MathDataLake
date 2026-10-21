import json
import sys
from pathlib import Path

import pyarrow.parquet as pq

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from configs.app import Config
from src.baseline.jsonl.numinaMath.method import (
    add_issue,
    content_key,
    create_report,
    prepare_record,
    validate_record,
)


# Đọc từng batch Parquet và cung cấp số dòng bắt đầu từ 1 trong file.
def read_records(path: Path):
    with pq.ParquetFile(path) as parquet:
        offset = 0
        for batch in parquet.iter_batches(batch_size=2048):
            for record in batch.to_pylist():
                offset += 1
                yield offset, record


# Lọc bản ghi lỗi, loại cặp trùng trong split và ghi JSONL tuần tự.
def process_file(path: Path, split: str, output, seen_pairs: dict,
                 train_problems: dict, report: dict) -> None:
    for row, raw in read_records(path):
        report["total_records"] += 1
        record = prepare_record(
            {"problem": None, "solution": None, **raw}, split, path.name, row,
            Config.NUMINA_REPO_ID, Config.NUMINA_REVISION,
        )
        reasons = validate_record(raw)
        if reasons:
            add_issue(report, "error", record, path.name, row, reasons)
            continue
        pair = content_key([record["problem"], record["solution"]])
        if pair in seen_pairs:
            add_issue(report, "error", record, path.name, row,
                      ["Trùng chính xác cặp (problem, solution) trong split"], seen_pairs[pair])
            continue
        problem = content_key(record["problem"])
        if split == "test" and problem in train_problems:
            add_issue(report, "warning", record, path.name, row,
                      ["Đề bài test xuất hiện trong train"], train_problems[problem])
        output.write(json.dumps(record, ensure_ascii=False) + "\n")
        seen_pairs[pair] = (path.name, row)
        if split == "train":
            train_problems.setdefault(problem, (path.name, row))
        report["saved_records"] += 1


# Chuyển train và test thành hai file data.jsonl, error.json.
def run_pipeline() -> dict:
    input_dir = Config.NUMINA_OUTPUT_DIR / "data"
    paths = {split: sorted(input_dir.glob(f"{split}-*.parquet")) for split in ("train", "test")}
    for split, files in paths.items():
        if not files:
            raise FileNotFoundError(f"Không tìm thấy NuminaMath {split} trong {input_dir}")
    output_dir = Config.ROOT / "results/jsonl/numinaMath"
    output_dir.mkdir(parents=True, exist_ok=True)
    report = create_report()
    train_problems = {}
    with (output_dir / "data.jsonl").open("w", encoding="utf-8", newline="\n") as output:
        for split, files in paths.items():
            seen_pairs = {}
            for path in files:
                process_file(path, split, output, seen_pairs, train_problems, report)
                print(f"Processed {path.name}", flush=True)
    (output_dir / "error.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    report = run_pipeline()
    print(f"NuminaMath: saved={report['saved_records']}, rejected={report['rejected_records']}, "
          f"warnings={report['warning_count']}")
