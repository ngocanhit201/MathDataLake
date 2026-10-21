import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DATASETS = ("numinaMath", "proofNet", "leanDojo")
SPLITS = {"train": "train", "test": "test", "val": "validation",
          "valid": "validation", "validation": "validation"}


# Chuẩn hóa xuống dòng, giữ nguyên Unicode, LaTeX và thụt dòng Lean.
def normalize_text(value):
    return value.replace("\r\n", "\n").replace("\r", "\n") if isinstance(value, str) else None


# Kiểm tra chuỗi bắt buộc mà không sửa nội dung nguồn.
def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


# Kiểm tra tọa độ khai báo [dòng, cột] theo quy ước nguồn.
def valid_position(value):
    return (isinstance(value, list) and len(value) == 2
            and all(type(item) is int for item in value)
            and value[0] >= 1 and value[1] >= 0)


# Kiểm tra trường chung và yêu cầu riêng của từng dataset.
def validate_record(record, dataset):
    if not isinstance(record, dict):
        return ["record_not_object"]
    required = {
        "numinaMath": ("problem", "solution"),
        "proofNet": ("nl_statement", "formal_statement", "src_header"),
        "leanDojo": ("formal_statement", "url", "commit", "file_path", "full_name"),
    }
    errors = [f"invalid_{key}" for key in ("id", "source_version", "split") + required[dataset]
              if not nonempty(record.get(key))]
    if record.get("split") not in SPLITS.values() and record.get("split") not in ("val", "valid"):
        errors.append("unsupported_split")
    if dataset == "proofNet" and not isinstance(record.get("nl_proof"), str):
        errors.append("invalid_nl_proof")
    if record.get("source") is not None and not isinstance(record["source"], str):
        errors.append("invalid_source")
    if dataset == "leanDojo":
        if record.get("strategy") is not None and not nonempty(record["strategy"]):
            errors.append("invalid_strategy")
        for key in ("start", "end"):
            if not valid_position(record.get(key)):
                errors.append(f"invalid_{key}")
        steps = record.get("traced_tactics")
        if not isinstance(steps, list):
            errors.append("invalid_traced_tactics")
        else:
            for index, step in enumerate(steps):
                if not isinstance(step, dict) or any(
                    not nonempty(step.get(key)) for key in ("tactic", "state_before", "state_after")
                ):
                    errors.append(f"invalid_tactic_{index}")
    return errors


# Ánh xạ một bản ghi hợp lệ về schema 1.0 và giữ dòng JSON gốc.
def map_record(record, dataset, input_file, input_line, raw_record):
    fields = {
        "numinaMath": ("problem", "solution", None, None, None),
        "proofNet": ("nl_statement", "nl_proof", "formal_statement", "src_header", "statement"),
        "leanDojo": (None, None, "formal_statement", None, "declaration_with_proof"),
    }
    statement, solution, lean, header, kind = fields[dataset]
    identity = json.dumps([dataset, record["source_version"], record["id"]], ensure_ascii=False)
    content = {
        "statement_text": normalize_text(record.get(statement)),
        "solution_text": normalize_text(record.get(solution)),
        "lean_code": normalize_text(record.get(lean)),
        "lean_header": normalize_text(record.get(header)),
        "lean_code_kind": kind,
        "lean_tactics": [
            {key: normalize_text(step[key]) for key in ("tactic", "state_before", "state_after")}
            for step in record.get("traced_tactics", [])
        ] if dataset == "leanDojo" else [],
    }
    metadata = {key: None for key in (
        "strategy", "repository_url", "repository_commit", "file_path",
        "declaration_name", "start", "end")}
    metadata.update(original_source=record.get("source"), original_split=record["split"])
    if dataset == "leanDojo":
        metadata.update(strategy=record.get("strategy"), repository_url=record["url"],
                        repository_commit=record["commit"], file_path=record["file_path"],
                        declaration_name=record["full_name"], start=record["start"], end=record["end"])
    return {
        "schema_version": "1.0", "id": hashlib.sha256(identity.encode("utf-8")).hexdigest(),
        "source_id": record["id"], "dataset": dataset, "source_version": record["source_version"],
        "split": SPLITS[record["split"]], "content": content, "metadata": metadata,
        "provenance": {"input_file": input_file, "input_line": input_line}, "raw_record": raw_record,
    }


# Đọc một dòng; trả về bản ghi chuẩn hóa hoặc lỗi có vị trí và nội dung gốc.
def parse_line(item, dataset, input_file):
    raw, index = item
    record = None
    try:
        record = json.loads(raw)
    except json.JSONDecodeError:
        reasons = ["invalid_json"]
    else:
        reasons = validate_record(record, dataset)
    if reasons:
        source_id = record.get("id") if isinstance(record, dict) else None
        return None, {"dataset": dataset, "source_id": source_id if isinstance(source_id, str) else None,
                      "input_file": input_file, "input_line": index + 1,
                      "reasons": reasons, "raw_record": raw}
    return map_record(record, dataset, input_file, index + 1, raw), None


# Định nghĩa schema Spark tường minh, kể cả các trường toàn null và mảng rỗng.
def create_schemas():
    from pyspark.sql.types import ArrayType, IntegerType, LongType, StringType, StructField, StructType

    string = StringType()
    tactic = StructType([StructField(key, string, False)
                         for key in ("tactic", "state_before", "state_after")])
    content = StructType([StructField(key, string) for key in (
        "statement_text", "solution_text", "lean_code", "lean_header", "lean_code_kind")]
        + [StructField("lean_tactics", ArrayType(tactic, False), False)])
    metadata = StructType([StructField(key, string, key != "original_split") for key in (
        "original_source", "original_split", "strategy", "repository_url",
        "repository_commit", "file_path", "declaration_name")]
        + [StructField(key, ArrayType(IntegerType(), False)) for key in ("start", "end")])
    provenance = StructType([StructField("input_file", string, False),
                             StructField("input_line", LongType(), False)])
    schema = StructType([StructField(key, string, False) for key in (
        "schema_version", "id", "source_id", "dataset", "source_version", "split")]
        + [StructField("content", content, False), StructField("metadata", metadata, False),
           StructField("provenance", provenance, False), StructField("raw_record", string, False)])
    error = StructType([
        StructField("dataset", string, False), StructField("source_id", string),
        StructField("input_file", string, False), StructField("input_line", LongType(), False),
        StructField("reasons", ArrayType(string, False), False), StructField("raw_record", string, False),
    ])
    return schema, error


# Đọc từng nguồn theo dòng, tạo vị trí ổn định và hợp nhất theo schema chung.
def read_sources(spark, input_dir):
    from functools import reduce
    from pyspark import StorageLevel

    schema, error_schema = create_schemas()
    frames, errors, cached = [], [], []
    for dataset in DATASETS:
        path = input_dir / dataset / "data.jsonl"
        if not path.is_file():
            raise FileNotFoundError(path)
        rows = spark.sparkContext.textFile(path.resolve().as_uri()).zipWithIndex()
        parsed = rows.map(lambda item, name=dataset, filename=path.as_posix():
                          parse_line(item, name, filename)).persist(StorageLevel.DISK_ONLY)
        cached.append(parsed)
        frames.append(spark.createDataFrame(parsed.filter(lambda pair: pair[0] is not None)
                                            .map(lambda pair: pair[0]), schema))
        errors.append(spark.createDataFrame(parsed.filter(lambda pair: pair[1] is not None)
                                            .map(lambda pair: pair[1]), error_schema))
    return (reduce(lambda left, right: left.unionByName(right), frames),
            reduce(lambda left, right: left.unionByName(right), errors), cached)


# Giữ bản đầu tiên theo file và dòng; ghi nhận các bản trùng ID còn lại.
def separate_duplicates(frame, errors):
    from pyspark.sql import Window, functions as F

    window = Window.partitionBy("id").orderBy("provenance.input_file", "provenance.input_line")
    ranked = frame.withColumn("_rank", F.row_number().over(window))
    duplicates = ranked.filter(F.col("_rank") > 1).select(
        "dataset", "source_id", F.col("provenance.input_file").alias("input_file"),
        F.col("provenance.input_line").alias("input_line"),
        F.array(F.lit("duplicate_id")).alias("reasons"), "raw_record")
    return ranked.filter(F.col("_rank") == 1).drop("_rank"), errors.unionByName(duplicates)


# Tính tỷ lệ bản ghi lỗi tổng thể và theo nguồn, tách số lý do khỏi số bản ghi.
def summarize(clean, errors):
    from pyspark.sql import functions as F

    saved = {row["dataset"]: row["count"] for row in clean.groupBy("dataset").count().collect()}
    rejected = {row["dataset"]: row["count"] for row in errors.groupBy("dataset").count().collect()}
    datasets = {}
    for dataset in DATASETS:
        good, bad = saved.get(dataset, 0), rejected.get(dataset, 0)
        datasets[dataset] = {"total_records": good + bad, "saved_records": good,
                             "rejected_records": bad, "error_rate": bad / (good + bad) if good + bad else 0.0}
    reasons = {row["reason"]: row["count"] for row in errors.select(
        F.explode("reasons").alias("reason")).groupBy("reason").count().collect()}
    total = sum(item["total_records"] for item in datasets.values())
    bad = sum(rejected.values())
    return {"schema_version": "1.0", "total_records": total, "saved_records": sum(saved.values()),
            "rejected_records": bad, "error_rate": bad / total if total else 0.0,
            "error_rate_unit": "fraction", "error_count": sum(reasons.values()),
            "errors_by_reason": reasons, "datasets": datasets}


# Ghi báo cáo và lần lượt các bản ghi lỗi, tránh gom toàn bộ lỗi vào RAM driver.
def write_report(path, report, errors):
    with path.open("w", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(report, ensure_ascii=False, indent=2)[:-2])
        output.write(',\n  "errors": [')
        separator = ""
        for row in errors.toLocalIterator():
            output.write(separator + "\n    " + json.dumps(row.asDict(recursive=True), ensure_ascii=False))
            separator = ","
        output.write("\n  ]\n}\n")


# Chạy Spark local, ghi chung Parquet và error.json; mặc định không ghi đè dữ liệu.
def run_pipeline(input_dir=ROOT / "results/jsonl", output_dir=ROOT / "results/parquet",
                 output_files=8, overwrite=False):
    from pyspark.sql import SparkSession
    from pyspark import StorageLevel

    if output_files < 1:
        raise ValueError("output_files phải >= 1")
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    if not overwrite and ((output_dir / "data").exists() or (output_dir / "error.json").exists()):
        raise FileExistsError("Đầu ra đã tồn tại; dùng --overwrite để thay thế")
    # Bản ghi Lean lớn: giới hạn batch cache để tránh cấp phát quá nhiều heap.
    spark = (SparkSession.builder.master("local[*]").appName("MathDataLake-Parquet-1.0")
             .config("spark.sql.inMemoryColumnarStorage.batchSize", 128).getOrCreate())
    cached = []
    clean = errors = None
    try:
        frame, errors, cached = read_sources(spark, input_dir)
        clean, errors = separate_duplicates(frame, errors)
        clean.persist(StorageLevel.DISK_ONLY)
        errors.persist(StorageLevel.DISK_ONLY)
        report = summarize(clean, errors)
        output_dir.mkdir(parents=True, exist_ok=True)
        clean.repartition(output_files).write.mode("overwrite" if overwrite else "errorifexists").option(
            "compression", "snappy").parquet((output_dir / "data").resolve().as_uri())
        write_report(output_dir / "error.json", report, errors)
        return report
    finally:
        for item in cached:
            item.unpersist()
        if clean is not None:
            clean.unpersist()
        if errors is not None:
            errors.unpersist()
        spark.stop()


# Nhận đường dẫn và số file đầu ra từ dòng lệnh.
def main():
    parser = argparse.ArgumentParser(description="Hợp nhất 3 nguồn JSONL thành Parquet schema 1.0")
    parser.add_argument("--input-dir", type=Path, default=ROOT / "results/jsonl")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/parquet")
    parser.add_argument("--output-files", type=int, default=8)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run_pipeline(args.input_dir, args.output_dir, args.output_files, args.overwrite),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
