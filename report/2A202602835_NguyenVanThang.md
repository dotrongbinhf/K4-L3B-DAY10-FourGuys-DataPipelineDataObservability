# Individual Report — Nguyễn Văn Thăng (2A202602835)

> Bản nháp này tổng hợp từ Git history và artifacts. Thành viên đứng tên cần rà soát, bổ sung trải nghiệm cá nhân và xác nhận nội dung trước khi nộp.

## Vai trò và bằng chứng

**Vai trò:** Crossref ingestion, raw data lineage và cleaning. Commit tiêu biểu: `d6e9520` (`Update craw data and clean data`) và `14d845a` (merge giữ ingestion mới nhất).

| Phần việc | File/artifact | Kết quả |
|---|---|---|
| Parse Crossref payload và fallback snapshot | `src/ingestion/crossref.py` | Chuẩn hóa DOI, title, abstract, authors, categories, dates và URLs thành `PaperRecord` |
| Bảo toàn dữ liệu nguồn | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | 24 records có raw response và parsed-record artifact |
| Tạo clean model | `src/ingestion/cleaning.py` | Deduplicate theo DOI, chuẩn hóa trường và tạo `age_days` cùng `text_for_embedding` |

## Kết quả thực tế

Clean dataset có 24 dòng. Mỗi embedding text ghép Title, Authors, Published, Categories và Summary. Baseline freshness report ghi ngày xuất bản trong khoảng 2026-04-01 đến 2026-09-15; không có dòng nào quá 180 ngày tại lần chạy 2026-09-26. Raw snapshot được dùng lại cho reproducible run và repair.

## Luồng và contract

Ingestion giữ raw response trước khi parse để có lineage và khả năng replay. Cleaning biến records thành schema phục vụ cả observability và retrieval. `paper_id` là DOI ổn định; `age_days` là chênh lệch giữa ngày chạy và `published`. Khi raw Crossref request không dùng được, pipeline có thể lấy dữ liệu từ local snapshot.

## Bằng chứng và điểm cần trình bày

Kiểm tra bằng các artifacts trong `data/raw/`, `data/clean/`, và quality report. Repair đọc lại raw snapshot nên không phụ thuộc corrupted dataframe. Khi demo, giải thích vì sao giữ raw tách biệt với clean data: raw là nguồn có thể tin cậy để tái tạo state sau biến đổi lỗi.

**Lưu ý cá nhân:** Bổ sung thời điểm/query lấy snapshot nếu bạn còn log ngoài repo; hiện artifact không lưu timestamp fetch riêng. Hãy thêm chi tiết về lỗi ingestion thực tế bạn đã xử lý trước khi nộp.
