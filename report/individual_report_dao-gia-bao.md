# Báo cáo cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Đào Gia Bảo |
| MSSV | DTB2324 |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | FourGuys |
| Vai trò chính | Tích hợp corruption, repair và phân tích tác động |
| Repository | [K4-L3B-DAY10-FourGuys-DataPipelineDataObservability](https://github.com/dotrongbinhf/K4-L3B-DAY10-FourGuys-DataPipelineDataObservability) |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Tích hợp luồng corruption → đánh giá → repair → so sánh | `src/pipelines/corruption_flow.py`: `repair_from_raw_snapshot`, `run_corruption_flow_pipeline` | Clean dataset, baseline metrics/quality, test set, raw snapshot | Corrupted/repaired dataset, metrics, quality reports, comparison report | Hoàn thành |
| Báo cáo tác động và recovery | `src/observability/reporting.py`: `generate_corruption_report`, bảng so sánh | Metrics và quality/freshness của ba trạng thái | `data/reports/corruption_report.md` | Hoàn thành |

Phạm vi đóng góp trực tiếp của tôi là Step 8, được ghi nhận trong commit `d3d63c6` (`feat: step 8`). Tôi không nhận ownership cho các module ingestion, cleaning, Step 6 baseline hoặc Step 7 corruption suite do các thành viên khác phụ trách; tôi tích hợp các đầu ra đó vào luồng cuối.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Module được phối hợp | Kết quả |
|---|---|---|
| Tích hợp và đối chiếu output giữa các giai đoạn | `src/ingestion/corruption.py`, `src/evaluation/metrics.py`, `src/observability/quality.py`, `src/retrieval/index.py` | Corrupted và repaired dùng chung benchmark; report khớp với các metrics và quality artifacts đã sinh |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Tạo corrupted dataset và đo ảnh hưởng | `run_corruption_flow_pipeline`, `data/clean/papers_clean_corrupted.json` | 20 dòng sau khi bỏ 5 bản ghi mới nhất và thêm một bản sao; quality gate báo FAIL | `data/quality/corrupted_quality_report.json`, `data/results/corrupted_metrics.json` |
| Khôi phục từ nguồn gốc và đánh giá lại | `repair_from_raw_snapshot`, `data/clean/papers_clean_repaired.json` | Tạo lại 24 dòng từ raw records, quality gate PASS | `data/quality/repaired_quality_report.json`, `data/results/repaired_metrics.json` |
| Tổng hợp so sánh | `generate_corruption_report`, `data/reports/corruption_report.md` | Báo cáo so sánh baseline/corrupted/repaired và cách phục hồi | Đối chiếu với ba metrics JSON và quality reports |

Kết quả chính: corrupted làm `retrieval_hit_rate` giảm từ **0.900** xuống **0.500** và `mean_token_f1` giảm từ **0.614** xuống **0.453**. Sau khi dựng lại từ raw snapshot, hai chỉ số trở về **0.900** và **0.614**, bằng baseline.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Cần đo được chất lượng RAG khi dữ liệu bị lỗi, chứng minh quality gate phát hiện dữ liệu không đạt, rồi khôi phục baseline từ nguồn tin cậy mà không dựa vào bản dữ liệu đã hỏng.

### Cách triển khai

`run_corruption_flow_pipeline` xác nhận trước các artifact Phase 1 cần thiết, đọc baseline và clean dataset, gọi corruption suite, lưu corrupted CSV/JSON và chạy quality checks. Trong thí nghiệm, pipeline vẫn index và đánh giá dữ liệu corrupted sau khi gate thất bại để đo tác động của “silent failure”; trong triển khai thật, dữ liệu lỗi cần bị chặn trước serving.

Phần repair đọc `crossref_records.json` (hoặc parse lại raw API response nếu raw records không có), gọi lại hàm cleaning chuẩn, kiểm tra quality và freshness, rồi mới lưu và index repaired dataset. Cả baseline, corrupted và repaired đều dùng cùng `test_set.json`, giúp so sánh trên cùng câu hỏi và ground truth. Cuối cùng, hàm reporting tổng hợp metric, quality và freshness thành một Markdown report.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | `papers_clean.json`, baseline metrics/quality, `test_set.json`, raw records hoặc raw Crossref response |
| Output | Corruption log, corrupted/repaired clean data, embeddings manifests, metrics, quality reports và `corruption_report.md` |
| Module phụ thuộc | `ingestion.corruption`, `ingestion.cleaning`, `evaluation.metrics`, `observability.quality`, `retrieval.index` |
| Module sử dụng output | Report nhóm, kiểm tra tác động dữ liệu và đối chiếu recovery |
| Điều kiện dừng | Thiếu Phase 1 artifact, thiếu nguồn raw để repair, repaired data không đạt quality/freshness gate |

### Cách xác minh

```bash
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Có baseline, corrupted và repaired artifacts; cùng 10 câu hỏi được dùng cho cả ba lần đánh giá.
- **Kết quả thực tế trong artifacts đã nộp:** Baseline PASS; corrupted FAIL quality; repaired PASS. Hit rate/F1 lần lượt là `0.900/0.614`, `0.500/0.453`, `0.900/0.614`.
- **Artifact đối chiếu:** `data/results/*_metrics.json`, `data/quality/*_quality_report.json`, `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Dữ liệu corrupted không đạt quality gate, nhưng lab cần lượng hóa suy giảm của agent.
- **Các phương án đã cân nhắc:** Dừng ngay tại gate; hoặc tiếp tục đánh giá như một nhánh thí nghiệm có gắn nhãn lỗi.
- **Phương án đã chọn:** Ghi quality FAIL, sau đó vẫn index/evaluate corrupted để tạo bằng chứng tác động trong môi trường lab.
- **Lý do:** Nếu dừng ngay sẽ chứng minh gate phát hiện lỗi nhưng không đo được hệ quả lên retrieval và câu trả lời. Luồng này dành cho thử nghiệm; chất lượng thất bại không được xem là dữ liệu đủ điều kiện phục vụ thật.
- **Bằng chứng:** Gate corrupted FAIL; hit rate giảm `0.400`, token F1 giảm khoảng `0.161` so với baseline. Sau repair, hai metrics trở về baseline.

## 6. Một lỗi hoặc blocker đã xử lý

Không có blocker runtime còn tồn đọng trong các artifact đã nộp. Trong luồng repair, tôi giữ nguồn sửa độc lập với corrupted dataset: dựng lại từ raw Crossref snapshot thay vì sửa chắp vá các dòng đã hỏng. Pipeline cũng dừng trước khi ghi/index repaired data nếu thiếu snapshot hoặc repaired data không qua quality/freshness gate. Đây là các guard cần thiết để tránh báo cáo recovery giả.

## 7. Hiểu biết về luồng end-to-end

1. Crossref response được lưu nguyên trạng và parse thành raw records. Cleaning chuẩn hóa text/list/date, loại bản ghi không hợp lệ và deduplicate theo `paper_id`; `text_for_embedding` ghép title, authors, published, categories và summary. Embedding được lập chỉ mục trong collection Chroma tương ứng.
2. Evaluation set chứa câu hỏi, ground truth và `ground_truth_doc_ids`. Retriever trả các document IDs; Hit Rate đo xem có ground-truth ID nào được truy xuất. Token F1 so sánh câu trả lời với ground truth theo tokenizer/chuẩn hóa của project.
3. Quality checks xác minh các expectation cấu trúc/nội dung như row count, non-null, ID uniqueness và độ dài summary. Freshness dùng `age_days` để tính tỷ lệ bản ghi cũ hơn 180 ngày; SLA cho phép tối đa 25% stale rows.
4. Dùng cùng test set giúp khác biệt metric phản ánh trạng thái dữ liệu/index hơn là do thay đổi câu hỏi hoặc đáp án chuẩn.
5. Repair thành công khi dữ liệu được tái tạo từ raw snapshot, quality/freshness đạt, repaired metrics được tính trên cùng test set và kết quả tiến về baseline. Trong lần chạy này, repaired khôi phục đúng baseline metrics.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
|---|---:|---:|---:|---|
| `retrieval_hit_rate` | 0.900 | 0.500 | 0.900 | Giảm 0.400 rồi phục hồi đầy đủ |
| `mean_token_f1` | 0.614 | 0.453 | 0.614 | Giảm khoảng 0.161 rồi phục hồi đầy đủ |
| `judge_accuracy` | 0.600 | 0.400 | 0.600 | Giảm 0.200 rồi trở lại baseline |
| `mean_judge_score` | 3.400 | 2.600 | 3.400 | Giảm 0.800 rồi trở lại baseline |
| Quality checks | PASS | FAIL | PASS | Corrupted fail ở uniqueness và summary length |
| Freshness status | PASS (0%) | PASS (5%) | PASS (0%) | SLA cho phép tối đa 25% stale rows |

Ragas không được chạy; artifact ghi rõ cần đặt `RUN_RAGAS=1` để bật bước này. Vì vậy, kết luận định lượng trong báo cáo dựa trên Hit Rate, Token F1 và judge metrics hiện có.

### Kết luận từ số liệu

1. Corruption đồng thời bỏ 5 bản ghi mới nhất, blank một summary, thêm noise, cắt ngắn title, lùi một ngày xuất bản và nhân bản một hàng → uniqueness và summary-length expectations thất bại → hit rate giảm từ 0.900 xuống 0.500, token F1 từ 0.614 xuống 0.453.
2. Repair dựng lại 24 dòng từ raw snapshot, sau đó kiểm tra và index lại → quality gate PASS → hit rate, token F1 và judge metrics đều quay về đúng baseline.

Thí nghiệm tiêm nhiều dạng corruption cùng lúc nên không đủ để kết luận riêng loại nào gây suy giảm lớn nhất. Bằng chứng quality xác định duplicate `paper_id` và summary rỗng là hai vi phạm được GX bắt trực tiếp. Ngày stale bị lùi 365 ngày nhưng freshness SLA vẫn PASS: chỉ 1/20 dòng (5%) stale, thấp hơn ngưỡng tối đa 25%. Đây là khác biệt giữa một expectation phát hiện lỗi trường hợp cụ thể và SLA theo tỷ lệ toàn tập.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Repair nên tái tạo từ raw snapshot bất biến để giữ data lineage và tránh phụ thuộc vào bản corrupted.
2. Một quality gate có thể báo vi phạm cụ thể trong khi một SLA theo tỷ lệ vẫn PASS; cần đọc cả chi tiết expectation lẫn freshness summary.
3. Quality failure không phải lúc nào cũng hiện ngay trong metric RAG; cần giữ log, kiểm định và metrics cùng nhau để giải thích nguyên nhân.

### Nếu có thêm thời gian

Chạy ablation từng corruption riêng, giữ nguyên test set và cấu hình index. Việc đó giúp tách ảnh hưởng của drop, blank, noise, title, stale date và duplicate; báo cáo được cả thay đổi metric và expectation tương ứng thay vì quy kết từ một thí nghiệm tổng hợp.

## 10. Cam kết của thành viên

- [x] Nội dung mô tả phạm vi Step 8 và phân biệt phần do thành viên khác sở hữu.
- [x] Các số liệu được đối chiếu với metrics/quality artifacts trong repository.
- [x] Không khẳng định Ragas đã chạy.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.

**Họ và tên:** Đào Gia Bảo

**MSSV:** DTB2324
**Ngày xác nhận:** 2026-09-26
