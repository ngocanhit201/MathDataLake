## **Quy tắc chung**

Funtion hóa tránh 1 hàm quá dài, trước mỗi funtion có 1 đoạn text ngắn nêu chức năng

### **1. Tạo dữ liệu**

- Nguồn tải lưu trong app.py
- File initData.py lấy các cấu hình từ app.py để tải dữ liệu

### **2. Tạo JSONL cho 3 nguồn dữ liệu**

Đọc riêng dữ liệu từ 3 nguồn code mỗi nguồn đặt src\baseline\jsonl\\[tên dữ liệu]

Tạo `method.py` chứa các hàm cần thiết cho `pipeline`. Hãy tìm hiểu trước về nguồn đang làm xem nên cần filter như nào

Tạo `pipeline.py`: đọc, xử lý ,filter, ghi kết quả vào results\jsonl\proofNet

Kết quả gồm 2 file; data.jsonl (kết quả dữ liệu sạch) error.json log tổng hợp về số lượng lỗi, số lượng bản ghi đã lưu, danh sách lỗi

**Ví dụ NuminaMath**

> Kế hoạch cho NuminaMath-CoT sẽ chỉ kiểm tra và làm sạch problem, solution; không dùng messages làm điều kiện filter.
>
> 1. Cấu trúc
>    src/baseline/jsonl/numinaMath/
>    ├── method.py
>    └── pipeline.py
>
> results/jsonl/numinaMath/
> ├── data.jsonl
> └── error.json
> 2. Quy tắc xử l
>
> problem, solution phải là chuỗi và không rỗng sau khi kiểm tra bằng .strip()
>
> - Giữ nguyên nội dung gốc: LaTeX, Unicode, khoảng trắng và xuống dòng.
> - Loại bản ghi trùng chính xác cặp (problem, solution) trong cùng split; giữ bản đầu tiên theo thứ tự tên file và dòng.
> - Giữ cùng đề nhưng khác lời giải.
> - Không bắt buộc lời giải chứa \boxed.
> - Giữ nguyên split; ghi cảnh báo khi đề trong test xuất hiện ở train.
>
> 3. Nội dung data.jsonl
>    Mỗi bản ghi gồm:
>    {
>    "id": "numinaMath🚋train-00000-of-00005:1",
>    "dataset": "AI-MO/NuminaMath-CoT",
>    "source_version": "<revision trong Config></revision>",
>    "source": "synthetic_math",
>    "split": "train",
>    "problem": "...",
>    "solution": "..."
>    }
>    Không xuất messages vì nội dung này lặp lại problem và solution. source được giữ làm thông tin nguồn gốc, không dùng để filter.
> 4. Nội dung error.json
>
> - total_records, saved_records, rejected_records.
> - error_count, errors: file nguồn, số dòng, ID và lý do loại. Lỗi trùng kèm vị trí bản được giữ.
> - warning_count, warnings: đề trùng giữa train và test; không loại bản ghi vì cảnh báo này.
>   Một bản ghi có thể có nhiều lý do lỗi, nên error_count có thể lớn hơn rejected_records.
>
> 5. Cách triển khai và kiểm tra
>    method.py chứa các hàm ngắn để kiểm tra hai trường, phát hiện trùng, chuẩn bị đầu ra và cập nhật log. Trước mỗi hàm có comment mô tả.
>    pipeline.py đọc từng file Parquet theo batch nhỏ bằng pyarrow, xử lý tuần tự rồi ghi ngay JSONL. Chưa đo hiệu năng.
>    Dựa trên khảo sát, dự kiến đọc 859.594, loại 6.641 bản ghi trùng và lưu 852.953 bản ghi; ghi 11 cảnh báo đề test xuất hiện trong train.

### **3 Đo hiệu năng jsonl**

Sửa file src\performance\jsonl\data.py

> Đọc từng dòng data.jsonl của 3 tệp dataset
> → Parse JSON
> → Đếm bản ghi thành công, ghi nhận lỗi đọc
>
> Ghi các chỉ số dưới vào file csv tại results\performance\jsonl\data.csv;
>
> | Chỉ số            | Ý nghĩa                                 |
> | ------------------- | ----------------------------------------- |
> | `elapsed_seconds` | Thời gian đọc và parse toàn bộ file |
> | `input_bytes`     | Dung lượng file JSONL trên đĩa       |
> | `rows_ok`         | Số bản ghi đọc thành công           |
> | `rows_error`      | Số dòng không parse được            |
> | `rows_per_second` | `rows_ok / elapsed_seconds`             |
> | `mb_per_second`   | Dung lượng đầu vào MB / thời gian   |
>
> Mỗi lần chạy lại sẽ lưu 1 bản ghi mới

### **4. Tạo chart jsonl**

Từ file src\performance\jsonl\chart.py tạo các biểu đồ

| Biểu đồ                            | Trục Y             | Mục đích                                          |
| ------------------------------------- | ------------------- | ---------------------------------------------------- |
| **Thời gian đọc và parse**  | `elapsed_seconds` | Cho thấy thời gian xử lý toàn bộ từng dataset |
| **Tốc độ theo dung lượng** | `mb_per_second`   | So sánh tốc độ xử lý dữ liệu theo MB/giây   |
| **Tốc độ theo bản ghi**     | `rows_per_second` | So sánh số bản ghi xử lý mỗi giây             |

Két quả lưu biểu đồ tại results\performance\jsonl

### **5. Tạo Parquet**

Dữ liệu bước trước

| Nguồn     | Nội dung hiện có                                                     | Điểm cần chú ý                                                         |
| ---------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| NuminaMath | `problem`,`solution`chứa text và LaTeX                            | `source`là nguồn con, ví dụ`synthetic_math`                         |
| ProofNet   | `nl_statement`,`nl_proof`,`formal_statement`,`src_header`       | Có cả nội dung tự nhiên và Lean                                       |
| LeanDojo   | `formal_statement`,`traced_tactics`, vị trí khai báo, repository | `formal_statement`mẫu đang chứa cả khai báo**và chứng minh** |

Schema chung


```
schema_version: string
id: string
source_id: string
dataset: string
source_version: string
split: stringcontent: struct
    statement_text: string?
    solution_text: string?
    lean_code: string?
    lean_header: string?
    lean_code_kind: string?
    lean_tactics: array
        tactic: string
        state_before: string
        state_after: stringmetadata: struct
    original_source: string?
    original_split: string
    strategy: string?
    repository_url: string?
    repository_commit: string?
    file_path: string?
    declaration_name: string?
    start: array?
    end: array?provenance: struct
    input_file: string
    input_line: longraw_record: string
```

Ánh sạ như sau: schema_v1.0

| Trường chung     | NuminaMath   | ProofNet             | LeanDojo                            |
| ------------------ | ------------ | -------------------- | ----------------------------------- |
| `statement_text` | `problem`  | `nl_statement`     | `null`                            |
| `solution_text`  | `solution` | `nl_proof`         | `null`                            |
| `lean_code`      | `null`     | `formal_statement` | `formal_statement`                |
| `lean_header`    | `null`     | `src_header`       | `null`                            |
| `lean_code_kind` | `null`     | `"statement"`      | `"declaration_with_proof"`        |
| `lean_tactics`   | `[]`       | `[]`               | Các bước trong`traced_tactics` |

Quy tắc đi kèm

- Các trường định danh, phiên bản và split phải là chuỗi không rỗng; id phải duy nhất.
- NuminaMath bắt buộc có đề và lời giải.
- ProofNet bắt buộc có phát biểu tự nhiên, Lean và header; lời chứng minh tự nhiên được phép rỗng theo baseline hiện tại.
- LeanDojo bắt buộc có mã Lean và thông tin vị trí khai báo; danh sách tactic được phép rỗng.
- Chuẩn hóa split val và valid về validation, đồng thời giữ giá trị gốc trong original_split.
- Giữ nguyên thụt dòng của Lean và nội dung công thức LaTeX.

Pipeline

Đọc riêng 3 nguồn jsonl, code ở src\baseline\parquet\pipeline.py
    → Ánh xạ về schema_v1.0
    → Hợp nhất thành một DataFrame
    → Kiểm tra dữ liệu
    → Ghi kết quả vào results\parquet, lỗi ghi tại results\parquet\error.json

Funtion hóa tránh 1 hàm quá dài, trước mỗi funtion có 1 đoạn text ngắn nêu chức năng


### **6 Đo hiệu năng parquet**

Sửa file src\performance\\parquet\data.py

> Đọc toàn bộ data  của 3 tệp dataset parquet_4,8,16
> → Đọc từng bản ghi
> Ghi các chỉ số dưới vào file csv tại results\performance\parquet\data.csv;
>
> | Chỉ số            | Ý nghĩa                                 |
> | ------------------- | ----------------------------------------- |
> | `elapsed_seconds` | Thời gian đọc và parse toàn bộ file |
> | `input_bytes`     | Dung lượng file trên đĩa             |
> | `rows_ok`         | Số bản ghi đọc thành công           |
> | `rows_per_second` | `rows_ok / elapsed_seconds`             |
> | `mb_per_second`   | Dung lượng đầu vào MB / thời gian   |
>
> Mỗi lần chạy lại sẽ lưu 1 bản ghi mới

### **7. Tạo chartParquet**



Từ file src\performance\parquet\chart.py tạo các biểu đồ, dữ liệu từresults\performance\parquet\data.csv



| File đầu ra           | Trục Y                                | Chiều tốt hơn |
| ----------------------- | -------------------------------------- | ---------------- |
| `elapsed_seconds.png` | Thời gian đọc và giải mã (giây) | Thấp hơn       |
| `mb_per_second.png`   | Tốc độ đọc (MB/giây)             | Cao hơn         |
| `rows_per_second.png` | Tốc độ đọc (bản ghi/giây)       | Cao hơn         |

Két quả lưu biểu đồ tại results\performance\parquet
