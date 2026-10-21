import csv
import json
from pathlib import Path
from time import perf_counter


# Đọc tuần tự từng dòng và đếm số JSON hợp lệ, không hợp lệ.
def count_records(path: Path) -> tuple[int, int]:
    rows_ok = rows_error = 0
    with path.open(encoding="utf-8") as source:
        for line in source:
            try:
                json.loads(line)
            except json.JSONDecodeError:
                rows_error += 1
            else:
                rows_ok += 1
    return rows_ok, rows_error


# Đo thời gian mở, đọc, parse, đóng file và tính tốc độ theo MB thập phân.
def measure_file(path: Path, dataset: str, run: int) -> dict:
    input_bytes = path.stat().st_size
    started = perf_counter()
    rows_ok, rows_error = count_records(path)
    elapsed = perf_counter() - started
    return {
        "dataset": dataset,
        "run": run,
        "elapsed_seconds": elapsed,
        "input_bytes": input_bytes,
        "rows_ok": rows_ok,
        "rows_error": rows_error,
        "rows_per_second": rows_ok / elapsed if elapsed > 0 else 0.0,
        "mb_per_second": input_bytes / 1_000_000 / elapsed if elapsed > 0 else 0.0,
    }


# Ghi số đo từng lượt vào CSV, thay thế kết quả của lần chạy trước.
def write_results(path: Path, results: list[dict]) -> None:
    fields = (
        "dataset", "run", "elapsed_seconds", "input_bytes", "rows_ok",
        "rows_error", "rows_per_second", "mb_per_second",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
