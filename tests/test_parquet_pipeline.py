import json
import os
import pytest

from src.baseline.parquet.pipeline import (
    DATASETS, create_schemas, map_record, normalize_text, parse_line,
    run_pipeline, validate_record, write_report,
)


# Tạo mẫu ba nguồn, cho phép chạy test mà không tải dataset lớn.
def sample_record(dataset):
    record = {**minimal_record(), "source": "synthetic_math" if dataset == "numinaMath" else dataset}
    if dataset == "proofNet":
        record.update(nl_statement=r"Prove $x=x$.", nl_proof="Reflexivity.", split="valid",
                      formal_statement="theorem x (n : Nat) : n = n :=", src_header="import X\n")
    if dataset == "leanDojo":
        record.update(formal_statement="lemma x (n : Nat) : n = n := by\n  rfl",
                      url="https://example.org/mathlib", commit="abc", file_path="X.lean",
                      full_name="x", start=[1, 0], end=[2, 5], strategy="random", split="val",
                      traced_tactics=[{"tactic": "rfl", "state_before": "n : Nat\n⊢ n = n",
                                       "state_after": "no goals", "annotated_tactic": ["rfl", []]}])
    return json.dumps(record, ensure_ascii=False)


# Kiểm tra ánh xạ, định danh ổn định, metadata và bảo toàn dòng nguồn.
@pytest.mark.parametrize("dataset", DATASETS)
def test_mapping_sources(dataset):
    raw = sample_record(dataset)
    record = json.loads(raw)
    result, error = parse_line((raw, 4), dataset, "data.jsonl")
    assert error is None
    assert result["schema_version"] == "1.0"
    assert result["source_id"] == record["id"]
    assert result["raw_record"] == raw
    assert result["provenance"] == {"input_file": "data.jsonl", "input_line": 5}
    assert result["metadata"]["original_split"] == record["split"]
    assert result["id"] == map_record(record, dataset, "other.jsonl", 8, raw)["id"]
    content = result["content"]
    if dataset == "numinaMath":
        assert content["statement_text"] == normalize_text(record["problem"])
        assert content["solution_text"] == normalize_text(record["solution"])
        assert result["metadata"]["original_source"] == record["source"]
        assert content["lean_code"] is None
    else:
        assert content["lean_code"] == normalize_text(record["formal_statement"])
    if dataset == "proofNet":
        assert content["statement_text"] == normalize_text(record["nl_statement"])
        assert content["solution_text"] == normalize_text(record["nl_proof"])
        assert content["lean_header"] == normalize_text(record["src_header"])
        assert content["lean_code_kind"] == "statement"
    if dataset == "leanDojo":
        assert content["lean_code_kind"] == "declaration_with_proof"
        assert len(content["lean_tactics"]) == len(record["traced_tactics"])
        assert result["metadata"]["repository_commit"] == record["commit"]


# Chuẩn hóa CRLF nhưng không thay công thức, Unicode, thụt dòng hoặc khoảng trắng cuối.
def test_normalize_preserves_math_and_indentation():
    assert normalize_text("  exact h  \r\n∀ x, x = x\r") == "  exact h  \n∀ x, x = x\n"
    assert normalize_text(r"Compute $\frac{a}{b}$.") == r"Compute $\frac{a}{b}$."
    assert normalize_text(None) is None


# Tạo dữ liệu NuminaMath tối thiểu cho các test không cần dữ liệu local.
def minimal_record():
    return {"id": "1", "source_version": "rev", "split": "train",
            "problem": "x", "solution": "y"}


# Kiểm tra giá trị split chuẩn và giá trị gốc được lưu riêng.
@pytest.mark.parametrize("split", ["val", "valid", "validation"])
def test_validation_split(split):
    record = {**minimal_record(), "split": split}
    result, error = parse_line((json.dumps(record), 0), "numinaMath", "input.jsonl")
    assert error is None
    assert result["split"] == "validation"
    assert result["metadata"]["original_split"] == split


# Kiểm tra ID khác nhau khi dataset hoặc phiên bản thay đổi.
def test_identity_includes_dataset_and_revision():
    record = minimal_record()
    first = map_record(record, "numinaMath", "a", 1, "")
    revised = map_record({**record, "source_version": "rev2"}, "numinaMath", "a", 1, "")
    other = map_record(record, "proofNet", "a", 1, "")
    assert len({first["id"], revised["id"], other["id"]}) == 3


# Sai kiểu, thiếu trường hoặc split không hỗ trợ đều phải trở thành bản ghi lỗi.
@pytest.mark.parametrize("patch,reason", [
    ({"problem": None}, "invalid_problem"), ({"solution": 12}, "invalid_solution"),
    ({"id": " "}, "invalid_id"), ({"source_version": ""}, "invalid_source_version"),
    ({"split": "unknown"}, "unsupported_split"), ({"split": []}, "invalid_split"),
])
def test_invalid_fields(patch, reason):
    raw = json.dumps({**minimal_record(), **patch})
    result, error = parse_line((raw, 7), "numinaMath", "input.jsonl")
    assert result is None
    assert reason in error["reasons"]
    assert error["input_line"] == 8
    assert error["raw_record"] == raw


# JSON hỏng, giá trị null hoặc mảng không được làm dừng toàn bộ pipeline.
@pytest.mark.parametrize("raw,reason", [("{", "invalid_json"), ("null", "record_not_object"),
                                      ("[]", "record_not_object")])
def test_invalid_json_records(raw, reason):
    result, error = parse_line((raw, 0), "numinaMath", "input.jsonl")
    assert result is None
    assert error["reasons"] == [reason]


# ProofNet cho phép lời chứng minh rỗng nhưng không cho phép null.
def test_empty_proof_is_allowed():
    record = {**minimal_record(), "nl_statement": "x", "formal_statement": "theorem x :=",
              "src_header": "import X", "nl_proof": ""}
    assert validate_record(record, "proofNet") == []
    record["nl_proof"] = None
    assert "invalid_nl_proof" in validate_record(record, "proofNet")


# LeanDojo chấp nhận danh sách tactic rỗng và kiểm tra cấu trúc từng bước.
def test_lean_positions_and_tactics():
    record = {**minimal_record(), "formal_statement": "lemma x := by\n  rfl",
              "url": "repo", "commit": "abc", "file_path": "X.lean", "full_name": "x",
              "start": [1, 0], "end": [2, 5], "traced_tactics": []}
    assert validate_record(record, "leanDojo") == []
    record.update(start=[True, 0], traced_tactics=[{"tactic": "rfl"}])
    assert "invalid_start" in validate_record(record, "leanDojo")
    assert "invalid_tactic_0" in validate_record(record, "leanDojo")


# Báo cáo dạng streaming vẫn phải tạo JSON hợp lệ khi có hoặc không có lỗi.
@pytest.mark.parametrize("records", [[], [{"reason": "invalid_json"}]])
def test_report_json(tmp_path, records):
    class Row:
        # Trả về dữ liệu lỗi như Spark Row.
        def asDict(self, recursive=False):
            return records[0]

    class Errors:
        # Mô phỏng iterator, không yêu cầu PySpark cho test định dạng JSON.
        def toLocalIterator(self):
            return iter([Row()] if records else [])

    path = tmp_path / "error.json"
    write_report(path, {"total_records": 1}, Errors())
    assert json.loads(path.read_text(encoding="utf-8")) == {"total_records": 1, "errors": records}


# Chạy Spark thực khi người dùng bật test tích hợp và môi trường đã sẵn sàng.
@pytest.mark.skipif(os.environ.get("RUN_SPARK_TESTS") != "1", reason="Đặt RUN_SPARK_TESTS=1 để chạy Spark")
def test_spark_end_to_end(tmp_path):
    pytest.importorskip("pyspark")
    from pyspark.sql import SparkSession

    input_dir = tmp_path / "input"
    for dataset in DATASETS:
        path = input_dir / dataset / "data.jsonl"
        path.parent.mkdir(parents=True)
        raw = sample_record(dataset)
        path.write_text(raw + "\n" + raw + "\n{\n", encoding="utf-8")
    output = tmp_path / "output"
    report = run_pipeline(input_dir, output, output_files=2)
    assert report["total_records"] == 9
    assert report["saved_records"] == 3
    assert report["rejected_records"] == 6
    assert report["errors_by_reason"] == {"invalid_json": 3, "duplicate_id": 3}
    assert report["error_rate"] == pytest.approx(6 / 9)
    assert len(json.loads((output / "error.json").read_text(encoding="utf-8"))["errors"]) == 6
    spark = SparkSession.builder.master("local[2]").appName("parquet-test").getOrCreate()
    try:
        frame = spark.read.parquet((output / "data").resolve().as_uri())
        expected, _ = create_schemas()
        assert frame.schema.simpleString() == expected.simpleString()
        assert frame.count() == 3
        assert {row["dataset"] for row in frame.select("dataset").collect()} == set(DATASETS)
        assert frame.filter("provenance.input_line != 1").count() == 0
    finally:
        spark.stop()
