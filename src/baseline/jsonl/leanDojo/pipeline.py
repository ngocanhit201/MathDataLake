import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from configs.app import Config
from src.baseline.jsonl.leanDojo.method import (
    add_error, create_report, declaration_key, load_corpus,
    prepare_record, validate_record,
)


# Đọc một mảng JSON gốc và trả về từng định lý cùng vị trí bắt đầu từ 1.
def read_records(path: Path):
    with path.open(encoding="utf-8") as source:
        records = json.load(source)
    if not isinstance(records, list):
        raise ValueError(f"Dữ liệu phải là mảng JSON: {path}")
    yield from enumerate(records, 1)


# Kiểm tra từng định lý, nối corpus và ghi tuần tự các bản ghi hợp lệ.
def process_split(path: Path, split: str, corpus: dict, output,
                  seen: dict, report: dict) -> None:
    stats = report["splits"][split]
    for row, record in read_records(path):
        report["total_records"] += 1
        stats["total_records"] += 1
        reasons = validate_record(record, corpus)
        if reasons:
            add_error(report, split, row, record, reasons)
            continue
        key = declaration_key(record)
        if key in seen:
            add_error(report, split, row, record,
                      ["Trùng vị trí khai báo trong cùng phiên bản mathlib"], seen[key])
            continue
        result = prepare_record(record, corpus, split, row, Config.LEANDOJO_VERSION)
        output.write(json.dumps(result, ensure_ascii=False) + "\n")
        seen[key] = (split, row)
        report["saved_records"] += 1
        stats["saved_records"] += 1
        if not record["traced_tactics"]:
            report["empty_traced_tactics"] += 1
            stats["empty_traced_tactics"] += 1


# Kiểm tra dữ liệu đầu vào và commit corpus trước khi tạo kết quả.
def check_inputs(root: Path) -> None:
    for relative in ("metadata.json", "corpus.jsonl", "random/train.json",
                     "random/val.json", "random/test.json"):
        if not (root / relative).is_file():
            raise FileNotFoundError(root / relative)
    metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    if metadata["from_repo"]["commit"] != Config.LEANDOJO_MATHLIB_REVISION:
        raise ValueError("Commit mathlib trong metadata không khớp Config")


# Chuyển cách chia random thành data.jsonl và báo cáo error.json.
def run_pipeline() -> dict:
    root = Config.LEANDOJO_OUTPUT_DIR / "leandojo_benchmark_4"
    check_inputs(root)
    corpus = load_corpus(root / "corpus.jsonl")
    report, seen = create_report(), {}
    output_dir = Config.ROOT / "results/jsonl/leanDojo"
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "data.jsonl").open("w", encoding="utf-8", newline="\n") as output:
        for split in report["splits"]:
            process_split(root / "random" / f"{split}.json", split, corpus, output, seen, report)
            print(f"Processed random/{split}.json", flush=True)
    (output_dir / "error.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    report = run_pipeline()
    print(f"LeanDojo: saved={report['saved_records']}, rejected={report['rejected_records']}, "
          f"empty_traced_tactics={report['empty_traced_tactics']}")
