# Member Role Report — Đỗ Trọng Bình

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Đỗ Trọng Bình |
| MSSV | 2A202602855 |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | FourGuys |
| Vai trò chính | Repair orchestration và impact reporting |
| Repository | https://github.com/dotrongbinhf/K4-L3B-DAY10-FourGuys-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Corruption/evaluation/repair flow | src/pipelines/corruption_flow.py | Baseline artifacts, clean data, test set, raw records | Corrupted và repaired artifacts | Hoàn thành |
| Comparison reporting | src/observability/reporting.py | Metrics, quality và freshness results | data/reports/corruption_report.md | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Tiêu thụ corruption log và dataframe | Đào Gia Bảo / ingestion/corruption.py | Corrupted output đi vào quality, indexing và evaluation |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Orchestrate corruption flow | corruption_flow.py | Corrupted 20 rows; repaired 24 rows | Pipeline output và clean JSON |
| Repair từ raw records | repair_from_raw_snapshot, repaired quality report | Rebuilt data qua quality/freshness gate | repaired_quality_report.json |
| So sánh ba trạng thái | reporting.py, corruption_report.md | Hit Rate/F1 phục hồi baseline | Đối chiếu ba metrics JSON |

Output cụ thể: report ghi baseline/corrupted/repaired Hit Rate 1.000/0.500/1.000 và Token F1 0.900/0.621/0.900.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Đo sự suy giảm khi corruption được index và xác nhận recovery từ nguồn tin cậy.

### Cách triển khai

Flow kiểm tra Phase 1 artifacts, ghi corrupted data và quality result, index/evaluate corruption dù gate FAIL để đo tác động, sau đó dựng repaired data từ raw records. Repaired chỉ được ghi/index sau khi quality và freshness pass. Cả ba trạng thái dùng chung test set; reporting đọc metrics/quality objects để tạo comparison table.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | Clean JSON, baseline metrics/quality, evaluation set, raw records |
| Output | Corruption log, corrupted/repaired data/manifests/metrics, comparison report |
| Module phụ thuộc | corruption.py, cleaning.py, quality.py, metrics.py, index.py |
| Module sử dụng output | Report nhóm và so sánh thực nghiệm |
| Điều kiện lỗi cần xử lý | Thiếu Phase 1 artifacts, thiếu raw source, repaired gate fail |

### Cách xác minh

~~~bash
LLM_PROVIDER=mock LLM_MODEL=mock .venv/bin/python script/run_corruption_flow.py
~~~

- **Kết quả mong đợi:** Có corrupted và repaired artifacts; repaired quality PASS.
- **Kết quả thực tế:** 20 corrupted rows/FAIL; 24 repaired rows/PASS; hit rate/F1 trở về baseline.
- **Artifact/log:** data/results/corrupted_metrics.json, repaired_metrics.json, data/reports/corruption_report.md.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Gate corrupted FAIL nhưng bài lab cần đo downstream impact.
- **Các phương án đã cân nhắc:** Dừng flow ngay tại gate; tiếp tục đánh giá nhánh có nhãn corrupted.
- **Phương án đã chọn:** Đánh giá corrupted branch, còn repaired branch bị chặn nếu không qua gate.
- **Lý do:** Nhánh thí nghiệm cần đo silent failure; repaired output phải đạt gate trước khi dùng.
- **Bằng chứng quyết định phù hợp:** Corrupted gate FAIL với hit rate 0.500; repaired gate PASS với hit rate 1.000.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Không có lỗi runtime cụ thể được lưu trong commit/artifact.
- **Lệnh hoặc bước tái hiện:** Gọi pipeline khi thiếu Phase 1 artifact hoặc raw snapshot.
- **Nguyên nhân gốc:** Repair không thể chứng minh recovery nếu thiếu baseline contract hoặc nguồn raw.
- **Cách xử lý:** Dừng sớm với lỗi cụ thể khi thiếu prerequisite; repair từ raw response/records.
- **Cách xác minh sau khi sửa:** Corruption flow sinh repaired quality PASS từ 24 rows.
- **Điều học được:** Recovery cần nguồn độc lập với corrupted data.

## 7. Hiểu biết về luồng end-to-end

1. Ingestion giữ raw source; cleaning tạo records dùng cho GX và embedding; index tạo collection riêng cho từng trạng thái.
2. Test set ghép question, ground truth và DOI để đánh giá retrieval hit cùng answer F1.
3. Quality gate kiểm tra từng expectation; freshness là SLA theo tỷ lệ stale records.
4. Cùng test set giúp so sánh ba trạng thái trên một benchmark.
5. Repair thành công khi raw rebuild qua gate, index lại và metrics phục hồi.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
|---|---:|---:|---:|---|
| retrieval_hit_rate | 1.000 | 0.500 | 1.000 | Rebuild phục hồi mức baseline |
| mean_token_f1 | 0.900 | 0.621 | 0.900 | Answer metric trở lại baseline |
| judge_accuracy | 0.900 | 0.600 | 0.900 | Heuristic fallback |
| mean_judge_score | 4.600 | 3.400 | 4.600 | Heuristic fallback |
| Quality checks | PASS | FAIL | PASS | Gate phân biệt damaged và rebuilt data |
| Freshness status | Fresh (0%) | Fresh (5%) | Fresh (0%) | Không vượt SLA 25% |

### Kết luận từ số liệu

1. Corrupted output có 20 rows, quality FAIL và hit/F1 suy giảm trên cùng benchmark.
2. Repair dùng raw records làm input độc lập, trả về 24 rows và PASS; hit/F1 phục hồi về 1.000/0.900.

Corruption nào ảnh hưởng rõ nhất và vì sao? Duplicate và blank summary có vi phạm expectation tương ứng; suite không tách riêng tác động từng mutation lên agent.

Kết quả nào khác với kỳ vọng ban đầu? Stale date tăng tỷ lệ lên 5% nhưng freshness vẫn PASS theo ngưỡng 25%.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Repair từ raw source tránh mang lỗi corrupted sang repaired output.
2. Gate result và downstream metrics cần xuất cùng nhau để giải thích silent failure.
3. Cùng test set là điều kiện để so sánh recovery với baseline.

### Nếu có thêm thời gian

Ghi hash raw snapshot trong report để liên kết mỗi lần repair với đúng source artifact.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa .env, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đỗ Trọng Bình

**Ngày xác nhận:** 2026-09-26
