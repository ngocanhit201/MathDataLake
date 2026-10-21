import json


# Đọc một dòng JSON và trả về lỗi cú pháp nếu có.
def parse_record(line: str) -> tuple[object, list[str]]:
    try:
        return json.loads(line), []
    except json.JSONDecodeError as error:
        return None, [f"JSON không hợp lệ: {error.msg}"]


# Kiểm tra các trường của ProofNet và ID đã xuất hiện.
def validate_record(record: object, seen_ids: set[str]) -> list[str]:
    if not isinstance(record, dict):
        return ["Bản ghi phải là JSON object"]
    errors = []
    for field in ("id", "nl_statement", "formal_statement", "src_header"):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} phải là chuỗi không rỗng")
    if not isinstance(record.get("nl_proof"), str):
        errors.append("nl_proof phải là chuỗi; cho phép chuỗi rỗng")
    identifier = record.get("id")
    if isinstance(identifier, str) and identifier in seen_ids:
        errors.append("id trùng với bản ghi đã lưu")
    return errors


# Giữ nguyên nội dung gốc và bổ sung thông tin nguồn, phiên bản, split.
def prepare_record(record: dict, split: str, revision: str) -> dict:
    return {**record, "source": "proofNet", "source_version": revision, "split": split}


# Khởi tạo báo cáo tổng hợp cho một lần chạy.
def create_report() -> dict:
    return {
        "total_records": 0,
        "saved_records": 0,
        "rejected_records": 0,
        "error_count": 0,
        "errors": [],
    }


# Ghi nhận vị trí và toàn bộ lý do loại một bản ghi.
def add_error(report: dict, source_file: str, line: int, record: object,
              reasons: list[str]) -> None:
    report["rejected_records"] += 1
    report["error_count"] += len(reasons)
    report["errors"].append({
        "source_file": source_file,
        "line": line,
        "record_id": record.get("id") if isinstance(record, dict) else None,
        "reasons": reasons,
    })
