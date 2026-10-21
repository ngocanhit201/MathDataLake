import json
from pathlib import Path


# Đọc chỉ mục phát biểu; đánh dấu None khi cùng khóa có nội dung khác nhau.
def load_corpus(path: Path) -> dict:
    corpus = {}
    with path.open(encoding="utf-8") as source:
        for line in source:
            entry = json.loads(line)
            for premise in entry["premises"]:
                key = (entry["path"], premise["full_name"])
                code = premise["code"]
                if key in corpus and corpus[key] != code:
                    corpus[key] = None
                else:
                    corpus[key] = code
    return corpus


# Kiểm tra tọa độ dòng, cột để định danh vị trí khai báo.
def valid_position(value: object) -> bool:
    return (isinstance(value, list) and len(value) == 2
            and all(type(item) is int for item in value)
            and value[0] >= 1 and value[1] >= 0)


# Kiểm tra các bước tactic; cho phép danh sách không có bước nào.
def validate_tactics(steps: object) -> list[str]:
    if not isinstance(steps, list):
        return ["traced_tactics phải là danh sách"]
    errors = []
    for number, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            errors.append(f"Tactic {number} phải là object")
            continue
        for field in ("tactic", "state_before", "state_after"):
            value = step.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"Tactic {number}: {field} phải là chuỗi không rỗng")
    return errors


# Kiểm tra thông tin định lý, phát biểu từ corpus và các bước chứng minh.
def validate_record(record: object, corpus: dict) -> list[str]:
    if not isinstance(record, dict):
        return ["Bản ghi phải là object"]
    errors = []
    for field in ("file_path", "full_name", "url", "commit"):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} phải là chuỗi không rỗng")
    for field in ("start", "end"):
        if not valid_position(record.get(field)):
            errors.append(f"{field} phải là vị trí [dòng, cột] hợp lệ")
    if all(isinstance(record.get(field), str) and record[field].strip()
           for field in ("file_path", "full_name")):
        code = corpus.get((record["file_path"], record["full_name"]))
        if not isinstance(code, str) or not code.strip():
            errors.append("Không tìm thấy phát biểu Lean hợp lệ trong corpus")
    errors.extend(validate_tactics(record.get("traced_tactics")))
    return errors


# Tạo khóa theo commit và vị trí, tránh nhận nhầm các khai báo cùng tên.
def declaration_key(record: dict) -> tuple:
    return (record["commit"], record["file_path"],
            tuple(record["start"]), tuple(record["end"]))


# Giữ trường gốc, thêm phát biểu từ corpus và thông tin nguồn, split.
def prepare_record(record: dict, corpus: dict, split: str, row: int,
                   version: str) -> dict:
    return {
        **record,
        "id": f"leanDojo:random:{split}:{row}",
        "source": "leanDojo",
        "source_version": version,
        "strategy": "random",
        "split": split,
        "formal_statement": corpus[(record["file_path"], record["full_name"])],
    }


# Khởi tạo thống kê chung và thống kê cho từng split.
def create_report() -> dict:
    return {
        "total_records": 0, "saved_records": 0, "rejected_records": 0,
        "error_count": 0, "errors": [], "empty_traced_tactics": 0,
        "splits": {
            split: {"total_records": 0, "saved_records": 0,
                    "rejected_records": 0, "empty_traced_tactics": 0}
            for split in ("train", "val", "test")
        },
    }


# Ghi vị trí bản ghi bị loại cùng các lý do và vị trí bản trùng nếu có.
def add_error(report: dict, split: str, row: int, record: object,
              reasons: list[str], duplicate_of: tuple | None = None) -> None:
    entry = {
        "source_file": f"random/{split}.json", "row": row,
        "record_id": f"leanDojo:random:{split}:{row}",
        "full_name": record.get("full_name") if isinstance(record, dict) else None,
        "reasons": reasons,
    }
    if duplicate_of is not None:
        entry["duplicate_of"] = {
            "source_file": f"random/{duplicate_of[0]}.json", "row": duplicate_of[1],
        }
    report["errors"].append(entry)
    report["error_count"] += len(reasons)
    report["rejected_records"] += 1
    report["splits"][split]["rejected_records"] += 1
