import sys
from pathlib import Path

# Cho phép chạy trực tiếp mà không trùng tên với thư viện chuẩn json.
if __package__ in (None, ""):
    sys.path[0] = str(Path(__file__).resolve().parents[2])

from configs.app import Config
from src.performance.jsonl.method import measure_file, write_results


# Kiểm tra đủ ba nguồn, đo tuần tự ba lượt mỗi nguồn và ghi CSV.
def run_benchmark() -> list[dict]:
    datasets = ("proofNet", "numinaMath", "leanDojo")
    paths = {name: Config.ROOT / "results/jsonl" / name / "data.jsonl" for name in datasets}
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    results = []
    for dataset, path in paths.items():
        for run in range(1, 4):
            result = measure_file(path, dataset, run)
            results.append(result)
            print(f"{dataset} run={run}: {result['elapsed_seconds']:.3f}s, "
                  f"rows_ok={result['rows_ok']}, rows_error={result['rows_error']}", flush=True)
    write_results(Config.ROOT / "results/performance/jsonl/data.csv", results)
    return results


if __name__ == "__main__":
    run_benchmark()
