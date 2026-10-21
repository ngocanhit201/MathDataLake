import csv
import json
import platform
from pathlib import Path
from time import perf_counter

import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[3]
CONFIGURATIONS = (4, 8, 16)
BATCH_SIZE = 1024
FIELDS = (
    "configuration", "run", "elapsed_seconds", "input_bytes", "rows_ok",
    "rows_error", "files_error", "rows_per_second", "mb_per_second",
)


# Kiểm tra header CSV và cấp số lượt chạy tiếp theo, giữ nguyên kết quả cũ.
def next_run(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 1
    with path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != list(FIELDS):
            raise ValueError(f"Header CSV không khớp: {path}")
        return max((int(row["run"]) for row in reader), default=0) + 1


# Đọc toàn bộ cột theo batch và giải mã thành bản ghi Python, không dùng metadata để đếm.
def read_records(files: list[Path]) -> tuple[int, list[dict]]:
    rows_ok = 0
    errors = []
    for path in files:
        try:
            with pq.ParquetFile(path) as parquet:
                for batch in parquet.iter_batches(batch_size=BATCH_SIZE, use_threads=False):
                    rows_ok += len(batch.to_pylist())
        except (OSError, pa.ArrowException, UnicodeError) as error:
            errors.append({"file": path.as_posix(), "reason": str(error)})
    return rows_ok, errors


# Đo đọc và giải mã; dung lượng chỉ tính file Parquet, tốc độ dùng MB thập phân.
def measure_configuration(files: list[Path], configuration: str, run: int) -> tuple[dict, list[dict]]:
    input_bytes = sum(path.stat().st_size for path in files)
    started = perf_counter()
    rows_ok, errors = read_records(files)
    elapsed = perf_counter() - started
    result = {
        "configuration": configuration,
        "run": run,
        "elapsed_seconds": elapsed,
        "input_bytes": input_bytes,
        "rows_ok": rows_ok,
        "rows_error": None if errors else 0,
        "files_error": len(errors),
        "rows_per_second": rows_ok / elapsed if not errors and elapsed > 0 else None,
        "mb_per_second": input_bytes / 1_000_000 / elapsed if not errors and elapsed > 0 else None,
    }
    return result, [{"configuration": configuration, **error} for error in errors]


# Ghi nối tiếp ba kết quả; chỉ ghi header khi CSV chưa có nội dung.
def append_results(path: Path, results: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    needs_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=FIELDS)
        if needs_header:
            writer.writeheader()
        writer.writerows(results)


# Kiểm tra đủ ba cấu hình, đo mỗi cấu hình một lượt và lưu lịch sử CSV cùng lỗi đọc.
def run_benchmark(root: Path = ROOT) -> list[dict]:
    output_dir = root / "results/performance/parquet"
    csv_path, error_path = output_dir / "data.csv", output_dir / "error.json"
    run = next_run(csv_path)
    history = json.loads(error_path.read_text(encoding="utf-8")) if error_path.exists() else {"runs": []}
    inputs = {}
    for count in CONFIGURATIONS:
        name = f"parquet_{count}"
        folder = root / "results" / name / "data"
        files = sorted(folder.glob("part-*.parquet"))
        if len(files) != count:
            raise ValueError(f"{folder}: cần {count} file Parquet, tìm thấy {len(files)}")
        inputs[name] = files
    results, errors = [], []
    for name, files in inputs.items():
        result, issues = measure_configuration(files, name, run)
        results.append(result)
        errors.extend(issues)
        print(f"{name} run={run}: {result['elapsed_seconds']:.3f}s, "
              f"rows_ok={result['rows_ok']}, files_error={result['files_error']}", flush=True)
    append_results(csv_path, results)
    history["runs"].append({
        "run": run, "engine": "pyarrow", "pyarrow_version": pa.__version__,
        "python_version": platform.python_version(), "batch_size": BATCH_SIZE,
        "use_threads": False, "configuration_order": list(inputs),
        "os_cache_cleared": False, "errors": errors,
    })
    error_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return results


if __name__ == "__main__":
    run_benchmark()
