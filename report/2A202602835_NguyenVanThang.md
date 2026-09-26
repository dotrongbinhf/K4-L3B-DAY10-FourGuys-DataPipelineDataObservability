# Member Role Report — Nguyễn Văn Thăng

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Nguyễn Văn Thăng |
| MSSV | 2A202602835 |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | FourGuys |
| Vai trò chính | Crossref ingestion, raw lineage và cleaning |
| Repository | https://github.com/dotrongbinhf/K4-L3B-DAY10-FourGuys-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Crossref parser/fetch | src/ingestion/crossref.py | Crossref response hoặc local snapshot | Raw response và PaperRecord list | Hoàn thành |
| Cleaning/data model | src/ingestion/cleaning.py | PaperRecord list | 24-row clean dataset và embedding text | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Cung cấp raw source cho repair | Đỗ Trọng Bình / corruption_flow.py | Repair đọc data/raw/crossref_records.json để dựng lại dữ liệu |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Parse và lưu nguồn Crossref | crossref.py, data/raw/ | 24 raw records và response snapshot | Đối chiếu raw artifacts |
| Chuẩn hóa clean schema | cleaning.py, papers_clean.csv, papers_clean.json | 24 unique rows với age_days và text_for_embedding | Check row count và baseline GX report |

Output cụ thể: 24 raw records được làm sạch thành 24 rows và được dùng lại làm nguồn repair.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Giữ được nguồn dữ liệu tái chạy và tạo schema ổn định cho observability, embedding và retrieval.

### Cách triển khai

Parser chuẩn hóa DOI, title, abstract/JATS, author, category, publication dates và URL; fetch lưu response gốc cùng parsed records, fallback về snapshot nếu request lỗi. Cleaning chuẩn hóa text/lists, loại dòng thiếu field bắt buộc, deduplicate DOI, tính age_days và ghép năm phần embedding text.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | Crossref response với message.items hoặc raw records JSON |
| Output | PaperRecord JSON, cleaned CSV/JSON |
| Module phụ thuộc | requests, core/config.py, core/utils.py |
| Module sử dụng output | cleaning.py, phase1.py, corruption_flow.py |
| Điều kiện lỗi cần xử lý | HTTP 429/5xx, response sai định dạng, DOI/title/date thiếu |

### Cách xác minh

~~~bash
LLM_PROVIDER=mock LLM_MODEL=mock .venv/bin/python script/run_phase1.py
~~~

- **Kết quả mong đợi:** Có 24 clean rows và baseline artifacts.
- **Kết quả thực tế:** 24 raw records tạo 24 clean rows; baseline quality PASS.
- **Artifact/log:** data/raw/crossref_response.json, data/raw/crossref_records.json, data/clean/papers_clean.json.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Crossref có thể không phản hồi hoặc trả lỗi rate-limit.
- **Các phương án đã cân nhắc:** Hủy pipeline khi API không sẵn sàng; hoặc replay từ raw snapshot đã lưu.
- **Phương án đã chọn:** Dùng local snapshot khi fetch thất bại, đồng thời không ghi đè raw response cũ khi fallback.
- **Lý do:** Giữ lineage và khả năng tái chạy khi nguồn ngoài không sẵn sàng.
- **Bằng chứng quyết định phù hợp:** Pipeline Phase 1 dùng source mode local raw snapshot và tạo 24 clean records.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Không có lỗi runtime cụ thể được ghi trong commit/artifacts.
- **Lệnh hoặc bước tái hiện:** Nhánh fallback trong fetch_source_records khi Crossref request ném RequestException.
- **Nguyên nhân gốc:** Pipeline phụ thuộc dịch vụ ngoài có thể rate-limit hoặc không truy cập được.
- **Cách xử lý:** Đọc và parse local Crossref response snapshot.
- **Cách xác minh sau khi sửa:** run_phase1.py tạo 24 clean rows từ snapshot.
- **Điều học được:** Raw snapshot cung cấp nguồn replay cho downstream pipeline và repair.

## 7. Hiểu biết về luồng end-to-end

1. Crossref response được giữ làm raw artifact, parser chuyển payload thành PaperRecord, cleaning tạo trường normalized và text_for_embedding, sau đó index sinh vectors.
2. Benchmark row gắn ground-truth DOI; retrieved IDs dùng cho Hit Rate và answer text so với reference bằng Token F1.
3. GX kiểm tra shape/completeness/uniqueness/content length; freshness tính tỷ lệ bản ghi trên 180 ngày.
4. Một evaluation set cố định giúp so sánh thay đổi do dữ liệu thay vì do benchmark.
5. Repair tải raw records, chạy lại cleaning/gate rồi index; 24 rows, PASS và baseline metrics là bằng chứng phục hồi.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
|---|---:|---:|---:|---|
| retrieval_hit_rate | 1.000 | 0.500 | 1.000 | Clean source khôi phục các hit bị mất |
| mean_token_f1 | 0.900 | 0.621 | 0.900 | F1 trở lại baseline |
| judge_accuracy | 0.900 | 0.600 | 0.900 | Heuristic fallback |
| mean_judge_score | 4.600 | 3.400 | 4.600 | Heuristic fallback |
| Quality checks | PASS | FAIL | PASS | Corrupted duplicate/summary length |
| Freshness status | Fresh (0%) | Fresh (5%) | Fresh (0%) | SLA pass ở cả ba |

### Kết luận từ số liệu

1. Corrupted data giảm còn 20 rows; quality phát hiện duplicate và summary rỗng, đồng thời Hit Rate/F1 giảm.
2. Re-ingestion từ raw records tái tạo 24 rows và quality PASS; retrieval/answer metrics bằng baseline.

Corruption nào ảnh hưởng rõ nhất và vì sao? Không tách được tác động từng mutation; duplicate/blank summary là vi phạm được GX xác nhận, còn các mutation kia được log để audit.

Kết quả nào khác với kỳ vọng ban đầu? Một row stale không làm freshness FAIL vì SLA xét tỷ lệ toàn tập, không báo động theo từng row.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Raw response và parsed records phục vụ hai bước khác nhau của lineage.
2. Chuẩn hóa schema trước khi embedding giúp retrieval và quality dùng cùng dữ liệu.
3. Snapshot fallback cho phép repair độc lập với trạng thái Crossref API.

### Nếu có thêm thời gian

Lưu timestamp và request parameters cùng snapshot để xác định thời điểm và điều kiện lấy dữ liệu.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa .env, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Văn Thăng

**Ngày xác nhận:** 2026-09-26
