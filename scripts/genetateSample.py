"""Xuất mẫu từ ba nguồn raw sang JSON, giữ nguyên các trường gốc.

Cài thư viện: python3 -m pip install pyarrow
Chạy: python3 scripts/genetateSample.py
Mặc định mỗi nguồn 1 bản ghi; đổi số lượng ở ba lời gọi cuối tệp.
"""

import json
import sys
from itertools import islice
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from configs.app import Config

SAMPLE_DIR = Config.ROOT / "data_sample"


def sampleNuminaMath(limit: int = 1) -> Path:
    """Đọc lần lượt các tệp Parquet của train, lấy limit bản ghi đầu."""
    import pyarrow.parquet as pq

    if limit < 1:
        raise ValueError("limit phải lớn hơn 0")
    records = []
    for path in sorted((Config.RAW_DATA / "numinaMath/data").glob("train-*.parquet")):
        for batch in pq.ParquetFile(path).iter_batches(batch_size=limit):
            records.extend(batch.to_pylist()[:limit - len(records)])
            if len(records) >= limit:
                break
        if len(records) >= limit:
            break
    if not records:
        raise ValueError("Không tìm thấy dữ liệu NuminaMath train trong raw")

    sample = {
        "source": Config.NUMINA_REPO_ID,
        "revision": Config.NUMINA_REVISION,
        "split": "train",
        "records": records,
    }
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    output = SAMPLE_DIR / "numinaMath.json"
    output.write_text(json.dumps(sample, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def sampleProofNet(limit: int = 1) -> Path:
    """Lấy limit bản ghi đầu từ benchmark/valid.jsonl."""
    if limit < 1:
        raise ValueError("limit phải lớn hơn 0")
    path = Config.RAW_DATA / "proofNet/benchmark/valid.jsonl"
    with path.open(encoding="utf-8") as source:
        records = [json.loads(line) for line in islice(source, limit)]
    sample = {
        "source": "https://github.com/zhangir-azerbayev/ProofNet",
        "source_file": "benchmark/valid.jsonl",
        "split": "valid",
        "records": records,
    }
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    output = SAMPLE_DIR / "proofNet.json"
    output.write_text(json.dumps(sample, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def sampleLeanDojo(limit: int = 1) -> Path:
    """Lấy mẫu random/val và xuất thêm corpus liên quan.

    Nối định lý: (file_path, full_name) -> (path, premises[].full_name).
    Nối premise trong annotated_tactic: (def_path, full_name) -> cùng khóa trên.
    Corpus mẫu chỉ giữ các khai báo cần nối; imports vẫn giữ đường dẫn gốc.
    """
    if limit < 1:
        raise ValueError("limit phải lớn hơn 0")
    root = Config.RAW_DATA / "leandojoBenchmark4v10/leandojo_benchmark_4"
    records = json.loads((root / "random/val.json").read_text(encoding="utf-8"))[:limit]
    needed = {(row["file_path"], row["full_name"]) for row in records}
    for row in records:
        for step in row["traced_tactics"]:
            for premise in step["annotated_tactic"][1]:
                needed.add((premise["def_path"], premise["full_name"]))

    corpus = []
    with (root / "corpus.jsonl").open(encoding="utf-8") as source:
        for line in source:
            entry = json.loads(line)
            entry["premises"] = [
                p for p in entry["premises"]
                if (entry["path"], p["full_name"]) in needed
            ]
            if entry["premises"]:
                corpus.append(entry)
    found = {(entry["path"], p["full_name"]) for entry in corpus for p in entry["premises"]}
    sample = {
        "version": "v10",
        "metadata": json.loads((root / "metadata.json").read_text(encoding="utf-8")),
        "split": "random/val",
        "corpus_file": "leanDojo_corpus.json",
        "records": records,
        "unresolved_references": [
            {"path": path, "full_name": name} for path, name in sorted(needed - found)
        ],
    }
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    output = SAMPLE_DIR / "leanDojo.json"
    output.write_text(json.dumps(sample, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (SAMPLE_DIR / "leanDojo_corpus.json").write_text(
        json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return output


if __name__ == "__main__":
    print(sampleNuminaMath(1))
    print(sampleProofNet(1))
    print(sampleLeanDojo(1))
