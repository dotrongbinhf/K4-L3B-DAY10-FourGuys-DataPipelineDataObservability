# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
|---|---|
| Khóa/Lớp | K4-L3B-DAY10 |
| Tên nhóm | FourGuys (theo tên repository) |
| Repository | https://github.com/dotrongbinhf/K4-L3B-DAY10-FourGuys-DataPipelineDataObservability |
| Ngày chạy kiểm chứng | 2026-09-26 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Deliverable |
|---:|---|---|---|---|
| 1 | Đào Gia Bảo | 2A202602793 | Corruption suite & pipeline integration | `src/ingestion/corruption.py`, `src/pipelines/phase1.py`, `tests/test_corruption.py` |
| 2 | Nguyễn Văn Thăng | 2A202602835 | Crossref ingestion & cleaning | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `data/raw/` |
| 3 | Đoàn Quang Thanh | 2A202602841 | Quality/evaluation verification & retrieval correctness | `src/retrieval/index.py`, `src/retrieval/qa.py`, baseline verification |
| 4 | Đỗ Trọng Bình | 2A202602855 | Repair orchestration & comparison reporting | `src/pipelines/corruption_flow.py`, `src/observability/reporting.py`, result artifacts |

## 2. Tóm tắt kết quả

Nhóm FourGuys xây dựng pipeline từ Crossref snapshot qua raw records, cleaning, Great Expectations 1.x, freshness monitoring, MiniLM embeddings và ChromaDB. Baseline được đánh giá bằng 10 câu hỏi trên cùng test set dùng cho corrupted và repaired. Baseline đạt retrieval hit rate 1.000, mean token F1 0.900, judge accuracy 0.900 và mean judge score 4.600. Bộ corruption tạo sáu loại lỗi; quality gate chuyển sang FAIL và retrieval hit rate giảm còn 0.500, token F1 còn 0.621. Repair dựng lại 24 dòng từ raw snapshot, vượt quality gate và khôi phục các metric về baseline. Freshness vẫn PASS khi corrupted vì chỉ 1/20 dòng (5%) vượt 180 ngày, dưới ngưỡng SLA 25%. Benchmark dùng heuristic judge; Ragas chưa có kết quả vì lời gọi Gemini thất bại do DNS không phân giải được `generativelanguage.googleapis.com`.

## 3. Kiến trúc và luồng dữ liệu

```text
Crossref response snapshot
  -> parsed raw records (24)
  -> cleaning / age_days / text_for_embedding
  -> Great Expectations + freshness gate
  -> MiniLM all-MiniLM-L6-v2 / ChromaDB
  -> 10-question baseline evaluation
  -> six corruption modes / corrupted evaluation
  -> rebuild from immutable raw records / repaired evaluation
  -> three-state comparison report
```

| Khối | Input và xử lý | Output | Owner |
|---|---|---|---|
| Ingestion | Crossref JSON; parse DOI, authors, dates, abstract; retry/fallback | `data/raw/crossref_response.json`, `crossref_records.json` | Nguyễn Văn Thăng |
| Cleaning | Normalize text, deduplicate `paper_id`, compute `age_days`, construct five-part embedding text | `data/clean/papers_clean.json` / `.csv` | Nguyễn Văn Thăng |
| Observability | GX 1.x row count, required non-null fields, unique DOI, summary length; freshness SLA | `data/quality/*_quality_report.json` | Đoàn Quang Thanh (review/verification) |
| Embedding/index | MiniLM 384-dimensional embeddings; persistent Chroma collections | `data/chroma/`, `data/embeddings/` | Đoàn Quang Thanh |
| Evaluation | Same 10 questions, ground-truth DOI; retrieval Hit Rate and token F1 | `data/results/*_metrics.json`, `*_answers.json` | Đoàn Quang Thanh |
| Corruption/repair | Six deterministic mutations; rebuild repaired data from raw records | corruption log, quality reports, comparison report | Đào Gia Bảo / Đỗ Trọng Bình |

## 4. Cách tái hiện kết quả

Cài dependency theo lockfile rồi chạy từ project root:

```bash
uv sync
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

Không cần LLM API key cho baseline hiện tại: QA benchmark trích trường từ tài liệu được retrieve; judge chạy heuristic khi `RUN_LLM_JUDGE` chưa bật. `RUN_RAGAS` mặc định tắt.

| Lệnh | Kết quả kiểm chứng gần nhất | Bằng chứng |
|---|---|---|
| `python script/run_phase1.py` | Thành công | `data/reports/phase1_report.md`, `data/results/baseline_metrics.json` |
| `python script/run_corruption_flow.py` | Thành công | `data/reports/corruption_report.md`, `data/results/corruption_log.json` |

## 5. Ingestion, cleaning và data contract

| Thuộc tính | Giá trị |
|---|---|
| Source | Crossref REST API; kiểm chứng lần cuối dùng local snapshot |
| Query | `agentic retrieval augmented generation large language model` |
| Số record raw | 24 |
| Số clean rows | 24 |
| Cơ chế fallback | Dùng raw Crossref snapshot khi request lỗi hoặc snapshot là nguồn được chọn |

Các trường clean chính gồm `paper_id`, `title`, `summary`, `authors`, `categories`, `published`, `updated`, `age_days`, `summary_chars` và `text_for_embedding`. Clean loại record thiếu DOI/title/summary hoặc ngày xuất bản không hợp lệ, chuẩn hóa whitespace, deduplicate theo DOI. `text_for_embedding` ghép Title, Authors, Published, Categories và Summary. `age_days` tính từ ngày chạy trừ ngày xuất bản.

## 6. Evaluation setup

| Thành phần | Giá trị |
|---|---|
| Số câu hỏi | 10 |
| Dạng câu hỏi | summary (3), authors (3), date (2), categories (2) |
| Ground truth | Câu trả lời lấy từ clean records; `ground_truth_doc_ids` chứa DOI |
| Embedding | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store | ChromaDB; `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| `top_k` | 4 |
| Judge | Heuristic token-F1 judge; LLM judge chưa bật |
| Test set dùng chung | `data/eval/test_set.json`; xác minh 10/10 câu và ground truth khớp trong cả ba answer artifacts |

Giữ nguyên test set để thay đổi metric phản ánh trạng thái dữ liệu/index, không phải thay đổi benchmark.

## 7. Kết quả baseline

| Metric | Giá trị | Diễn giải |
|---|---:|---|
| `retrieval_hit_rate` | 1.000 | 10/10 câu có ground-truth DOI trong kết quả retrieval |
| `mean_token_f1` | 0.900 | Token F1 trung bình với ground truth |
| `judge_accuracy` | 0.900 | Tỷ lệ đúng theo heuristic judge |
| `mean_judge_score` | 4.600 / 5 | Điểm heuristic trung bình |
| Ragas | Chưa hoàn tất | Key đã cấu hình; provider hostname `generativelanguage.googleapis.com` không phân giải được từ môi trường chạy |

## 8. Data quality và freshness

| Check | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| GX quality gate | PASS | FAIL | PASS |
| Rows | 24 | 20 | 24 |
| Unique `paper_id` | PASS | FAIL (duplicate) | PASS |
| Summary length ≥ 30 | PASS | FAIL (blank summary) | PASS |
| Stale ratio (`age_days > 180`) | 0.0% | 5.0% (1/20) | 0.0% |
| Freshness SLA (max 25%) | PASS | PASS | PASS |

Quality checks kiểm tra schema/completeness/uniqueness/độ dài; freshness theo dõi độ cũ theo SLA riêng. Corrupted freshness PASS là kết quả đúng vì stale ratio 5% chưa vượt ngưỡng 25%.

## 9. Corruption scenarios và repair

| Corruption | Số tác động | Signal | Repair |
|---|---:|---|---|
| Drop latest records | 5 dòng bị loại | Mất dữ liệu mới; còn 19 dòng trước bước duplicate | Rebuild từ raw snapshot |
| Blank summary | 1 | Summary length fail | Rebuild từ raw snapshot |
| Inject noise | 1 | Nhiễu trong nội dung/index text | Rebuild từ raw snapshot |
| Truncate title | 1 | Hư title và embedding text | Rebuild từ raw snapshot |
| Stale date | 1 | `age_days` tăng 365 ngày; freshness vẫn trong SLA tổng thể | Rebuild từ raw snapshot |
| Duplicate rows | 1 dòng được nhân bản | Unique DOI fail; cuối cùng 20 rows | Rebuild từ raw snapshot |

Log có 10 event: 5 dropped rows và một event cho mỗi corruption còn lại. Repair không sửa bản corrupted tại chỗ; nó dựng clean data lại từ `data/raw/crossref_records.json`, chạy gate rồi tạo repaired collection.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| `retrieval_hit_rate` | 1.000 | 0.500 | 1.000 |
| `mean_token_f1` | 0.900 | 0.621 | 0.900 |
| `judge_accuracy` | 0.900 | 0.600 | 0.900 |
| `mean_judge_score` | 4.600 | 3.400 | 4.600 |
| GX quality gate | PASS | FAIL | PASS |
| Freshness SLA | PASS | PASS | PASS |

Corruption làm Hit Rate giảm 0.500 và token F1 giảm 0.279; quality gate phát hiện trùng DOI và summary rỗng. Repair từ raw phục hồi 24 dòng, các expectation PASS và metrics về đúng mức baseline. Cả ba đánh giá dùng cùng 10 câu hỏi/ground truth.

## 11. Vấn đề tích hợp quan trọng

Manifest Chroma ban đầu chứa đường dẫn tuyệt đối từ máy Windows, còn benchmark đưa title trong câu hỏi vào exact lookup, làm Hit Rate không phản ánh vector search. Đã sửa loader để dùng đường dẫn theo project config, manifest ghi `data/chroma`, và evaluation dùng kết quả vector search. Chạy lại Phase 1 và corruption flow; baseline mới được sinh từ lần chạy này.

## 12. Giới hạn và hướng cải thiện

| Giới hạn | Ảnh hưởng | Cải thiện |
|---|---|---|
| Heuristic judge; Ragas chưa có kết quả | Không thay thế được đánh giá bởi LLM/faithfulness metrics | Chạy lại `RUN_RAGAS=1` trong môi trường có thể truy cập Gemini API |
| Demo hiện không có dashboard | Không có biểu đồ live | Trình chiếu console/report hoặc làm dashboard nếu nhóm còn thời gian |
| Raw snapshot không lưu thời điểm fetch/query metadata riêng | Khó audit chính xác thời điểm nguồn được lấy | Ghi ingestion manifest có timestamp, params và source hash |

## 13. Checklist trước khi nộp

- [x] Baseline pipeline chạy exit code 0.
- [x] Corruption flow chạy exit code 0.
- [x] `tests/test_corruption.py` — 1 test passed.
- [x] Corruption report có bảng ba trạng thái.
- [x] Có đủ baseline/corrupted/repaired metrics.
- [x] Điền tên, MSSV, vai trò vào `docs/TEAM.md` và báo cáo nhóm; vai trò được đối chiếu với commit history.
- [x] Có bốn báo cáo cá nhân theo MSSV trong `report/`.
- [x] Mỗi thành viên đã rà soát và xác nhận báo cáo cá nhân.
- [x] Mỗi thành viên có commit trong lịch sử nhánh `main`.
- [ ] Mỗi cá nhân nộp repository link lên VLearn LMS.
- [ ] Demo/Q&A trực tiếp với giảng viên.
- [x] Không có `.env` trong working tree; không ghi API key vào báo cáo.
