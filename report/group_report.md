# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
|---|---|
| Khóa/Lớp | K4-L3B |
| Tên nhóm | FourGuys |
| Repository | https://github.com/dotrongbinhf/K4-L3B-DAY10-FourGuys-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
|---:|---|---|---|---|
| 1 | Đào Gia Bảo | 2A202602793 | Corruption suite và baseline integration | `src/ingestion/corruption.py`, `src/pipelines/phase1.py` |
| 2 | Nguyễn Văn Thăng | 2A202602835 | Crossref ingestion, raw lineage và cleaning | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py` |
| 3 | Đoàn Quang Thanh | 2A202602841 | Retrieval correctness, index portability và evaluation verification | `src/retrieval/qa.py`, `src/retrieval/index.py` |
| 4 | Đỗ Trọng Bình | 2A202602855 | Repair orchestration và impact reporting | `src/pipelines/corruption_flow.py`, `src/observability/reporting.py` |

## 2. Tóm tắt kết quả

Nhóm hoàn thiện ingestion Crossref, cleaning, kiểm định Great Expectations 1.x và freshness, vector hóa bằng `all-MiniLM-L6-v2`, cùng ba lượt đánh giá trên cùng benchmark. Baseline tạo 24 clean records, 24 vector documents, quality PASS và retrieval hit rate 1.000. Bộ benchmark có 10 câu thuộc summary, authors, date và categories; baseline đạt mean token F1 0.900. Corruption suite ghi log sáu loại lỗi: bỏ năm record mới nhất, blank summary, inject noise, truncate title, stale date và duplicate row. Dataset corrupted còn 20 dòng; uniqueness và summary-length expectations FAIL, freshness vẫn PASS ở stale ratio 5%. Retrieval hit rate giảm còn 0.500 và token F1 còn 0.621. Repair dựng lại dữ liệu từ raw snapshot, tạo 24 dòng, qua quality gate và đưa các chỉ số retrieval/token F1 về baseline. Judge dùng heuristic trong lần xác minh offline; timestamp fetch Crossref không được lưu nên thời điểm lấy dữ liệu không thể khôi phục chính xác.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

Điều chỉnh sơ đồ dưới đây nếu cách triển khai thực tế của nhóm khác starter:

```text
Crossref API hoặc local snapshot
    -> raw response và parsed records
    -> clean DataFrame / age_days / text_for_embedding
    -> Great Expectations và freshness check
    -> all-MiniLM-L6-v2 / ChromaDB
    -> baseline evaluation
    -> sáu corruption / corrupted evaluation
    -> repair từ raw records / repaired evaluation
    -> report ba trạng thái
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
|---|---|---|---|---|
| Ingestion | Crossref works API hoặc raw snapshot | Retry các lỗi HTTP tạm thời, parse DOI/title/abstract/author/date; fallback snapshot | `data/raw/crossref_response.json`, `crossref_records.json` | Nguyễn Văn Thăng |
| Cleaning | Parsed `PaperRecord` | Chuẩn hóa text/lists/dates, loại record thiếu field bắt buộc, deduplicate DOI, tính tuổi và embedding text | `data/clean/papers_clean.csv`, `.json` | Nguyễn Văn Thăng |
| Embedding/index | Clean DataFrame | MiniLM normalized vectors và metadata trong Chroma | `data/embeddings/`, `data/chroma/` | Đoàn Quang Thanh |
| Evaluation | Index và `data/eval/test_set.json` | Vector search `top_k=4`, Hit Rate, Token F1, judge metrics | `data/results/*_metrics.json`, `*_answers.json` | Đoàn Quang Thanh |
| Observability | Clean/corrupted/repaired DataFrame | Bốn GX expectations và freshness SLA | `data/quality/*_quality_report.json` | Đoàn Quang Thanh (verification) |
| Corruption/repair | Clean DataFrame và raw snapshot | Sáu mutation có log; rebuild repaired từ raw records | Corruption log, corrupted/repaired data | Đào Gia Bảo / Đỗ Trọng Bình |
| Orchestration | Paths/config và pipeline artifacts | Chạy baseline; corruption → evaluation → repair → comparison | `data/reports/phase1_report.md`, `corruption_report.md` | Đào Gia Bảo / Đỗ Trọng Bình |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
|---|---|
| `LLM_PROVIDER` | `mock` (override trong lệnh xác minh offline) |
| `LLM_MODEL` | `mock` (override trong lệnh xác minh offline) |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 ngày; tối đa 25% stale records |
| Random seed, nếu có | Không sử dụng |

Không lưu API key trong repository. Các metrics judge của lần xác minh offline dùng heuristic fallback.

### Lệnh cài đặt

Chỉ giữ lại cách nhóm đã dùng.

```bash
uv sync
```

### Lệnh chạy

Baseline:

```bash
LLM_PROVIDER=mock LLM_MODEL=mock .venv/bin/python script/run_phase1.py
```

Corruption flow:

```bash
LLM_PROVIDER=mock LLM_MODEL=mock .venv/bin/python script/run_corruption_flow.py
```

`mock` giữ lần xác minh độc lập với mạng; benchmark trích field từ tài liệu được vector-retrieved và judge dùng heuristic fallback.

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
|---|---|---|---|
| Baseline pipeline | Thành công | 2026-09-26 15:14 GMT+7 | `baseline_metrics.json`, `baseline_quality_report.json`, `phase1_report.md` |
| Corruption flow | Thành công; corrupted quality FAIL theo thiết kế, repaired PASS | 2026-09-26 15:14 GMT+7 | Corruption log, ba metrics JSON, `corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
|---|---|
| Source | Crossref Works API; artifact hiện có từ local snapshot |
| Query/filter | `agentic retrieval augmented generation large language model`; filter `from-pub-date:2026-03-30,has-abstract:true` tại lần chạy 2026-09-26 |
| Thời điểm lấy dữ liệu | Không được lưu trong raw artifacts |
| Số record nhận được | 24 |
| Cơ chế retry/backoff | Tối đa 3 lần; HTTP 429/5xx chờ lần lượt 0.5 và 1 giây; sau lỗi dùng local snapshot |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
|---|---|---|---|---|
| Raw `DOI` / clean `paper_id` | String | Có | Định danh bài báo | Bỏ record thiếu; lowercase và deduplicate |
| Raw `title` / clean `title` | String hoặc list / string | Có | Tiêu đề | Lấy/chuẩn hóa title; bỏ nếu rỗng |
| Raw `abstract` / clean `summary` | String / string | Có | Tóm tắt | Bỏ JATS/HTML tags; bỏ record thiếu |
| Raw `author` / clean `authors` | List[object] / list[string] | Không | Danh sách tác giả | Ghép given/family; dùng `Unknown` nếu trống |
| Raw `subject` / clean `categories` | List[string] / list[string] | Không | Lĩnh vực | Chuẩn hóa; dùng `Uncategorized` nếu trống |
| Raw publication date / clean `published` | Date-parts object / ISO date | Có | Ngày xuất bản | Thử các trường Crossref theo thứ tự; loại ngày không hợp lệ |
| Clean `age_days` | Integer | Có | Số ngày từ xuất bản tới ngày chạy | Tính từ `published`; dùng cho freshness |
| Clean `text_for_embedding` | String | Có | Nội dung đưa vào embedding | Ghép Title, Authors, Published, Categories, Summary |

### Quy tắc cleaning

| Quy tắc | Quality dimension liên quan | Số record bị tác động | Cách xác minh |
|---|---|---:|---|
| Bỏ HTML/JATS và chuẩn hóa whitespace/list/date | Validity/consistency | 24 được xử lý; số dòng thực sự đổi không được log | `papers_clean.json` |
| Loại record thiếu DOI/title/summary hoặc ngày sai | Completeness/validity | 0 bị loại trong snapshot này | 24 parsed records và 24 clean rows |
| Deduplicate theo DOI (case-insensitive) | Uniqueness | 0 bị loại trong snapshot này | Clean `paper_id` unique |
| Sinh `age_days` và `text_for_embedding` năm phần | Freshness/retrieval readiness | 24 rows | Clean schema và quality report |

`paper_id` dùng DOI lowercase. `text_for_embedding` nối lần lượt title, authors, published date, categories và summary. `age_days` được tính bằng ngày chạy trừ ngày xuất bản.

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
|---|---|
| Số câu hỏi | 10 |
| Các `question_type` | summary (3), authors (3), date (2), categories (2) |
| Ground-truth document ID | DOI trong `ground_truth_doc_ids`; so với IDs trả về từ vector retrieval |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection | ChromaDB: `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| Retrieval `top_k` | 4 |
| LLM provider/model | `mock` / `mock` trong lần xác minh offline; judge heuristic |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json`, 10 IDs `eval_001`–`eval_010` |

Test set giữ nguyên để chênh lệch metric phản ánh trạng thái dữ liệu/index. Ba answer artifacts có cùng câu hỏi, ground truth và DOI.

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái | Ghi chú |
|---|---|---|---|
| Raw response/records | `data/raw/` | Có | 24 items/records |
| Cleaned dataset | `data/clean/` | Có | CSV và JSON, 24 dòng |
| Embedding manifest/index | `data/embeddings/`, `data/chroma/` | Có | Ba collection, 24/20/24 documents |
| Evaluation set | `data/eval/test_set.json` | Có | 10 câu, đủ bốn loại |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | Hit Rate, Token F1 và judge metrics |
| Quality/freshness | `data/quality/` | Có | Baseline/corrupted/repaired reports |
| Baseline report | `data/reports/phase1_report.md` | Có | Được pipeline sinh |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
|---|---:|---|
| `retrieval_hit_rate` | 1.000 | 10/10 câu lấy ground-truth DOI trong vector top-k |
| `mean_token_f1` | 0.900 | F1 trung bình của câu trả lời với ground truth |
| `judge_accuracy` | 0.900 | Heuristic judge; không phải LLM judgment |
| `mean_judge_score` | 4.600 / 5 | Điểm heuristic trung bình |
| Ragas, nếu có | N/A | Không thuộc evaluator thực tế của pipeline |

## 8. Data quality và freshness

### Quality checks

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
|---|---|---|---|---|
| `ExpectTableRowCountToBeBetween` | Volume | 5–5000 rows | PASS, 24 | `baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` | Completeness | `paper_id`, `title`, `text_for_embedding` | PASS, 0 null | `baseline_quality_report.json` |
| `ExpectColumnValuesToBeUnique` | Uniqueness | `paper_id` | PASS, 0 duplicates | `baseline_quality_report.json` |
| `ExpectColumnValueLengthsToBeBetween` | Content validity | `summary` ≥30 chars | PASS, 0 unexpected | `baseline_quality_report.json` |

### Freshness

| Thuộc tính | Giá trị |
|---|---|
| Freshness được đo tại | Clean dataset, qua `age_days` |
| Timestamp mới nhất | 2026-09-15 |
| Ngưỡng freshness | `age_days > 180`; stale ratio tối đa 25% |
| Trạng thái baseline | Fresh |
| Lý do | 0/24 rows stale; `data/quality/freshness_report.json` |

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
|---|---|---:|---|---|---|
| Drop latest records | Loại 20% mới nhất theo published date | 5 | Mất bản ghi mới; GX không có completeness check cho benchmark coverage | Tổng hit rate giảm trong bộ corruption kết hợp | Rebuild từ raw |
| Blank summary | Gán summary rỗng | 1 | Summary length fail | Corrupted quality FAIL | Rebuild từ raw |
| Inject noise | Thêm chuỗi rác vào summary | 1 | Nội dung embedding nhiễu; GX bắt buộc không có noise check | Tác động chỉ đo cùng các mutation khác | Rebuild từ raw |
| Truncate title | Giữ 6 ký tự đầu title | 1 | Trường vẫn non-null; không có title-length expectation | Tác động chỉ đo cùng các mutation khác | Rebuild từ raw |
| Stale date | Lùi published 365 ngày | 1 | Stale count tăng | Stale ratio 5%, SLA vẫn PASS | Rebuild từ raw |
| Duplicate rows | Nhân bản một hàng | 1 | DOI uniqueness fail | Corrupted quality FAIL | Rebuild từ raw |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: 10 events, đủ sáu loại mutation và paper ID/field/value cần thiết.

Repair nạp lại `data/raw/crossref_records.json`, chạy cleaning, quality/freshness và tạo collection repaired riêng. Không sửa trực tiếp corrupted rows.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét |
|---|---:|---:|---:|---:|---:|---|
| `retrieval_hit_rate` | 1.000 | 0.500 | 1.000 | -0.500 | +0.500 | Về baseline |
| `mean_token_f1` | 0.900 | 0.621 | 0.900 | -0.279 | +0.279 | Về baseline |
| `judge_accuracy` | 0.900 | 0.600 | 0.900 | -0.300 | +0.300 | Heuristic judge |
| `mean_judge_score` | 4.600 | 3.400 | 4.600 | -1.200 | +1.200 | Heuristic judge |
| Quality checks pass/fail | PASS | FAIL | PASS | PASS→FAIL | FAIL→PASS | Corrupted: duplicate và summary length |
| Freshness status | PASS (0%) | PASS (5%) | PASS (0%) | Stale +5 pp | Stale -5 pp | Cả ba không vượt 25% SLA |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. Corruption kết hợp bỏ record mới nhất, blank summary và duplicate làm uniqueness/summary-length checks FAIL; trên cùng test set hit rate giảm 1.000→0.500 và Token F1 giảm 0.900→0.621. Các mutation chạy cùng lượt nên không tách riêng mức tác động từng loại.
2. Repair dựng lại từ raw records tạo 24 clean rows, quality trở lại PASS và evaluation cùng test set đưa hit rate/Token F1 về 1.000/0.900.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** Baseline benchmark từng có thể trả Hit Rate 1.0 dù retrieval vector không đưa ground-truth DOI lên đầu.
- **Nguyên nhân:** Câu hỏi benchmark chứa title trong dấu nháy và QA dùng exact-title lookup để đẩy paper đó lên kết quả.
- **Cách xử lý:** Loại exact-title lookup khỏi `answer_question`; giữ evaluation trên kết quả `index.search()` vector-only.
- **Cách xác minh:** Chạy `LLM_PROVIDER=mock uv run python script/run_phase1.py`; đối chiếu `baseline_answers.json` để thấy retrieved IDs đến từ vector search và Hit Rate được tính trên các IDs đó.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
|---|---|---|
| Lần xác minh dùng mock provider và heuristic judge | Metrics không đánh giá LLM judge | Chạy evaluator với provider hỗ trợ nếu cần LLM-based judgment |
| Raw artifact không lưu timestamp/query metadata riêng của lần fetch | Không thể khôi phục chính xác thời điểm lấy snapshot | Lưu fetch timestamp và request parameters cùng raw snapshot |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
