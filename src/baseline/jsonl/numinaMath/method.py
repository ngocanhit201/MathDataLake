import hashlib
import json


# Kiểm tra đề bài và lời giải, không thay đổi nội dung gốc.
def validate_record(record: dict) -> list[str]:
    return [
        f"{field} phải là chuỗi không rỗng"
        for field in ("problem", "solution")
        if not isinstance(record.get(field), str) or not record[field].strip()
    ]


# Tạo mã băm ổn định cho nội dung dùng để phát hiện trùng chính xác.
def content_key(value: object) -> bytes:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).digest()


# Tạo bản ghi đầu ra và ID theo vị trí gốc, không xuất messages.
def prepare_record(record: dict, split: str, filename: str, row: int,
                   dataset: str, revision: str) -> dict:
    return {
        "id": f"numinaMath:{split}:{filename.removesuffix('.parquet')}:{row}",
        "dataset": dataset,
        "source_version": revision,
        "source": record.get("source"),
        "split": split,
        "problem": record["problem"],
        "solution": record["solution"],
    }


# Khởi tạo thống kê bản ghi, lỗi và cảnh báo của một lần chạy.
def create_report() -> dict:
    return {
        "total_records": 0,
        "saved_records": 0,
        "rejected_records": 0,
        "error_count": 0,
        "errors": [],
        "warning_count": 0,
        "warnings": [],
    }


# Ghi vị trí lỗi hoặc cảnh báo, kèm vị trí bản trùng nếu có.
def add_issue(report: dict, kind: str, record: dict, filename: str, row: int,
              reasons: list[str], duplicate_of: tuple | None = None) -> None:
    entry = {
        "source_file": f"data/{filename}",
        "row": row,
        "record_id": record["id"],
        "reasons": reasons,
    }
    if duplicate_of is not None:
        entry["duplicate_of"] = {
            "source_file": f"data/{duplicate_of[0]}", "row": duplicate_of[1],
        }
    report[f"{kind}s"].append(entry)
    report[f"{kind}_count"] += len(reasons)
    if kind == "error":
        report["rejected_records"] += 1
