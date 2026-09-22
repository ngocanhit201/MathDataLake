# MathDataLake
## Hiện trạng
- Đã lấy được dữ liêu từ 3 nguồn
## Cấu trúc và yêu cầu bàn giao (Theo đề bài)

| Tệp / Thư mục | Nội dung yêu cầu |
| --- | --- |
| `README.md` | Mục tiêu, kiến trúc, hướng dẫn cài đặt, dữ liệu, lệnh chạy nhanh và cách tái tạo kết quả chính. |
| `src/` | Mã nguồn được tổ chức có cấu trúc. |
| `tests/` | Các kiểm thử. |
| `configs/` | Cấu hình cho từng thí nghiệm. |
| `data_sample/` | Dữ liệu mẫu được phép sử dụng hợp pháp. |
| `scripts/` | Script tải hoặc tạo dữ liệu đầy đủ. |
| `results/raw/` | Kết quả thô. |
| `results/figures/` | Bảng và hình được tạo bằng script. |
| `docs/` | Data card, model/system card, AI-use statement và ghi chú về quyền riêng tư/giấy phép (privacy/license note). |
| `report.pdf` hoặc `report.docx` | Báo cáo dài 8–12 trang. |
| `slides/demo/` | Slide và kịch bản trình diễn. |
| `contributions.md` | Vai trò, issue, pull request và phần bảo vệ của từng thành viên. |


## Mô tả file
initData: tạo dữ liệu

## To do
### YÊU CẦU DỮ IỆU
```
Không tải và đưa toàn bộ dữ liệu lớn vào Git. Chỉ lưu sample hợp pháp, manifest, checksum và script tải/tạo dữliệu. Mọi split phải cố định và được version hóa

Hiện tại project chỉ tải về theo commit cố định; không có manifest, checksum.... theo yêu cầu
```
=> Cần lưu theo yêu cầu

## Kế hoạch thực hiện 10 tuần

### Tuần 1
Nhiệm vụ bắt buộc: Khảo sát nguồn, giấy phép, trường dữ liệu; chốt câu hỏi và lược đồ bản nháp.
Minh chứng cần nộp: Đề cương 1 trang; danh mục nguồn; sơ đồ lược đồ v0.1.
Mô tả: 

### Tuần 2
Nhiệm vụ bắt buộc: Tải snapshot nhỏ; xây manifest và data contract; tạo 100–1.000 bản ghi mẫu.
Minh chứng cần nộp: Raw sample; checksum; data contract; script đọc được cả ba nguồn.
Mô tả:

### Tuần 3
Nhiệm vụ bắt buộc: Cài baseline JSONL + Python tuần tự; đo thời gian và dung lượng.
Minh chứng cần nộp: Baseline chạy end-to-end; raw timing; báo cáo lỗi đọc.
Mô tả:

### Tuần 4
Nhiệm vụ bắt buộc: Cài Spark ETL; chuẩn hóa text, LaTeX, Lean và metadata; thêm test.
Minh chứng cần nộp: Pipeline Spark v0.1; kiểm thử lược đồ; báo cáo tỷ lệ lỗi.
Mô tả:

### Tuần 5
Nhiệm vụ bắt buộc: Thiết kế Parquet, partition và kích thước tệp; xử lý small-file problem.
Minh chứng cần nộp: Ba cấu hình lưu trữ; bảng số tệp, dung lượng, thời gian đọc.
Mô tả:

### Tuần 6
Nhiệm vụ bắt buộc: Bổ sung provenance, catalog và cơ chế cập nhật gia tăng.
Minh chứng cần nộp: Data card; catalog; thử nghiệm thêm một batch dữ liệu mới.
Mô tả:

### Tuần 7
Nhiệm vụ bắt buộc: Chạy 10K, 100K và toàn bộ dữ liệu; lặp ít nhất 3 lần.
Minh chứng cần nộp: CSV kết quả thô; biểu đồ runtime, throughput, RAM, bytes I/O.
Mô tả:

### Tuần 8
Nhiệm vụ bắt buộc: Ablation: JSONL/Parquet, có/không partition, nhiều tệp nhỏ/tệp hợp lý.
Minh chứng cần nộp: Bảng ablation; phân tích điểm nghẽn và trường hợp lỗi.
Mô tả:

### Tuần 9
Nhiệm vụ bắt buộc: Đóng gói kho mẫu, mã, truy vấn và báo cáo dạng bài báo ngắn.
Minh chứng cần nộp: Release candidate; README; bản báo cáo; demo script.
Mô tả:

### Tuần 10
Nhiệm vụ bắt buộc: Tích hợp API dữ liệu cho nhóm khác; demo và bảo vệ cá nhân.
Minh chứng cần nộp: Bản bàn giao cuối; video/demo; bảng đóng góp cá nhân.
Mô tả:
