import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from configs.app import Config
from src.baseline.jsonl.proofNet.method import (
    add_error,
    create_report,
    parse_record,
    prepare_record,
    validate_record,
)


# Đọc tuần tự một split, lọc lỗi và ghi bản ghi hợp lệ vào JSONL.
def process_split(source, output, split: str, revision: str,
                  seen_ids: set[str], report: dict) -> None:
    for number, line in enumerate(source, 1):
        report["total_records"] += 1
        record, reasons = parse_record(line)
        if not reasons:
            reasons = validate_record(record, seen_ids)
        if reasons:
            add_error(report, f"benchmark/{split}.jsonl", number, record, reasons)
            continue
        result = prepare_record(record, split, revision)
        output.write(json.dumps(result, ensure_ascii=False) + "\n")
        seen_ids.add(record["id"])
        report["saved_records"] += 1


# Chuyển hai split ProofNet thành data.jsonl và báo cáo error.json.
def run_pipeline() -> dict:
    input_dir = Config.PROOFNET_OUTPUT_DIR / "benchmark"
    splits = ("valid", "test")
    for split in splits:
        if not (input_dir / f"{split}.jsonl").is_file():
            raise FileNotFoundError(input_dir / f"{split}.jsonl")
    output_dir = Config.ROOT / "results/jsonl/proofNet"
    output_dir.mkdir(parents=True, exist_ok=True)
    report = create_report()
    seen_ids = set()
    with (output_dir / "data.jsonl").open("w", encoding="utf-8", newline="\n") as output:
        for split in splits:
            with (input_dir / f"{split}.jsonl").open(encoding="utf-8") as source:
                process_split(source, output, split, Config.PROOFNET_REVISION, seen_ids, report)
    (output_dir / "error.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    report = run_pipeline()
    print(f"ProofNet: saved={report['saved_records']}, rejected={report['rejected_records']}")
