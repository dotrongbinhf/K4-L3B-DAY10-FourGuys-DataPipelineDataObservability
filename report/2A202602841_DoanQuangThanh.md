# Member Role Report — Đoàn Quang Thanh

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Đoàn Quang Thanh |
| MSSV | 2A202602841 |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | FourGuys |
| Vai trò chính | Retrieval correctness, vector index portability và evaluation verification |
| Repository | https://github.com/dotrongbinhf/K4-L3B-DAY10-FourGuys-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Vector index path portability | src/retrieval/index.py | Settings và embedding manifest | Index load theo project Chroma path | Hoàn thành |
| Retrieval/evaluation correctness | src/retrieval/qa.py | Benchmark question và vector index | Vector-only retrieved IDs và field-specific answer | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Đối chiếu quality gate và testset artifacts | Nguyễn Văn Thăng / quality.py, testset.py | Xác minh GX baseline PASS và 10 câu benchmark đủ bốn loại |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Bỏ exact-title shortcut trong evaluation | qa.py, baseline_answers.json | Hit Rate đo IDs từ vector search | So ground-truth DOI với retrieved_doc_ids |
| Chuyển manifest sang đường dẫn tương đối | index.py, papers_embeddings.json | Manifest dùng data/chroma và load qua settings | Đọc manifest, load ba collection |
| Xác minh ba trạng thái | Ba metrics JSON và test set | Hit/F1: 1.000/0.900 → 0.500/0.621 → 1.000/0.900 | Đối chiếu artifacts |

Output cụ thể: ba answer artifacts chứa cùng 10 question/ground-truth pairs.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Đảm bảo Hit Rate đánh giá retrieval thực và Chroma manifests không phụ thuộc đường dẫn máy cá nhân.

### Cách triển khai

Benchmark question có paper title; exact lookup từ title sẽ biết trước ground-truth paper nên không thể dùng để chấm retrieval. QA benchmark dùng vector index.search(); answer extractor lấy authors/date/categories/summary từ metadata của retrieved document đầu tiên. Manifest ghi relative path, còn loader dùng path trong project settings.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | Question, Settings, collection Chroma và manifest |
| Output | Retrieved DOI/context/title cùng câu trả lời |
| Module phụ thuộc | retrieval/index.py, core/config.py |
| Module sử dụng output | evaluation/metrics.py, agent.py |
| Điều kiện lỗi cần xử lý | Collection/manifest thiếu hoặc không có kết quả retrieval |

### Cách xác minh

~~~bash
LLM_PROVIDER=mock LLM_MODEL=mock .venv/bin/python script/run_phase1.py
~~~

- **Kết quả mong đợi:** Hit Rate tính từ vector results và manifest mở đúng project index.
- **Kết quả thực tế:** Baseline Hit Rate 1.000; manifest dùng relative path; corrupted Hit Rate 0.500.
- **Artifact/log:** data/embeddings/*.json, data/results/*_answers.json.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Title xuất hiện nguyên văn trong benchmark question.
- **Các phương án đã cân nhắc:** Dùng title làm exact lookup hoặc chỉ vector-search trong evaluator.
- **Phương án đã chọn:** Vector-only retrieval cho benchmark.
- **Lý do:** Exact lookup sẽ leak ground-truth document và làm Hit Rate giả tạo.
- **Bằng chứng quyết định phù hợp:** Answer artifact có retrieved DOI do search trả về; corrupted Hit Rate giảm 0.500 trên cùng test set.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Manifest index chứa absolute path từ máy khác nên không portable.
- **Lệnh hoặc bước tái hiện:** Load manifest ở một project path khác.
- **Nguyên nhân gốc:** Loader tin persist_path đã serialize thay vì project config.
- **Cách xử lý:** Lưu relative path và resolve bằng settings.paths.chroma_dir.
- **Cách xác minh sau khi sửa:** Load baseline/corrupted/repaired collections qua ba manifests trong cùng project.
- **Điều học được:** Artifact path là một phần của portability contract.

## 7. Hiểu biết về luồng end-to-end

1. Parsed Crossref records qua cleaning rồi embed vào Chroma; metadata paper ID được giữ cùng vector/context.
2. Benchmark gắn ground-truth DOI với từng question; Hit Rate kiểm tra retrieved IDs, Token F1 đánh giá answer text.
3. GX kiểm tra constraints trên dataset; freshness kiểm tra tuổi dữ liệu theo SLA riêng.
4. Giữ benchmark cố định để so trạng thái index/dataset.
5. Repair được xác nhận bằng repaired dataset 24 rows, quality PASS và retrieval/F1 phục hồi baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
|---|---:|---:|---:|---|
| retrieval_hit_rate | 1.000 | 0.500 | 1.000 | Vector-only evaluation vẫn nhận đúng DOI baseline |
| mean_token_f1 | 0.900 | 0.621 | 0.900 | Phục hồi khi index dựng lại từ raw |
| judge_accuracy | 0.900 | 0.600 | 0.900 | Heuristic fallback |
| mean_judge_score | 4.600 | 3.400 | 4.600 | Heuristic fallback |
| Quality checks | PASS | FAIL | PASS | Duplicate và summary length fail |
| Freshness status | Fresh (0%) | Fresh (5%) | Fresh (0%) | Tỷ lệ stale không vượt SLA |

### Kết luận từ số liệu

1. Corruption làm quality FAIL và vector Hit Rate giảm từ 1.000 xuống 0.500 trên cùng benchmark.
2. Repaired index được xây dựng từ raw source, quality PASS và retrieval metric trở về baseline.

Corruption nào ảnh hưởng rõ nhất và vì sao? Chỉ kết luận được tác động corruption kết hợp; duplicate và blank summary có signal trực tiếp, các loại khác không được ablation riêng.

Kết quả nào khác với kỳ vọng ban đầu? Vector Hit Rate vẫn 1.000 sau khi bỏ exact lookup; retrieved IDs xác nhận benchmark tìm document bằng vector search.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Benchmark leakage có thể làm Hit Rate cao mà không đo retrieval cần đánh giá.
2. Portable loader nên dùng project configuration thay vì absolute path trong manifest.
3. Retrieval IDs và answer quality là tín hiệu riêng, cần đối chiếu cả hai.

### Nếu có thêm thời gian

Đánh giá thêm query không chứa paper title để kiểm tra semantic retrieval ngoài benchmark hiện có.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa .env, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đoàn Quang Thanh

**Ngày xác nhận:** 2026-09-26
