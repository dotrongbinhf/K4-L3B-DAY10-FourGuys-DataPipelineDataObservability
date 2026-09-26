# Individual Report — Đoàn Quang Thanh (2A202602841)

> Bản nháp này tổng hợp từ phần review/verification trong phiên làm việc và Git commits của thành viên. Hãy tự xác nhận nội dung cá nhân trước khi nộp.

## Vai trò và bằng chứng

**Vai trò:** Quality/evaluation verification, retrieval correctness và portability của vector index. Commits tiêu biểu: `119872d` (`fix retrieval evaluation and portable index paths`) và `a7c0413` (`refresh baseline artifacts with vector retrieval`).

| Phần việc | File/artifact | Kết quả |
|---|---|---|
| Bỏ đường dẫn machine-specific trong manifest | `src/retrieval/index.py`, `data/embeddings/papers_embeddings.json` | Manifest lưu `data/chroma`; load dùng path theo project settings |
| Bảo đảm Hit Rate đo vector retrieval | `src/retrieval/qa.py` | Bỏ exact-title lookup có thể leak tài liệu ground truth; dùng `index.search()` |
| Đồng bộ loại câu hỏi và câu trả lời | `src/retrieval/qa.py` | Nhận diện authors, categories, date đúng với benchmark questions |
| Xác minh quality gate/test set | `src/observability/quality.py`, `src/evaluation/testset.py` | GX success=True; tạo đủ 10 câu thuộc 4 nhóm |

## Kết quả thực tế

Trên cùng test set, baseline metrics sau lần chạy 2026-09-26 là Hit Rate 1.000, token F1 0.900, heuristic judge accuracy 0.900 và score 4.600. Corrupted đạt 0.500 / 0.621 / 0.600 / 3.400. Repaired trở về baseline. Tất cả ba answer artifacts có cùng 10 question/ground-truth pairs.

## Quyết định kỹ thuật

Exact-title lookup tiện cho truy vấn trực tiếp, nhưng không phù hợp trong benchmark vì câu hỏi sinh ra đã chứa nguyên title. Dùng lookup để đưa tài liệu đúng lên đầu làm Hit Rate không còn đo vector index. Tách exact lookup khỏi evaluation và giữ nó trong tool lookup của agent. Tương tự, manifest chỉ lưu đường dẫn tương đối; loader dùng đường dẫn chuẩn từ cấu hình project để hoạt động trên máy khác.

## Quality và freshness

GX gate dùng row count, non-null columns, uniqueness và summary length. Freshness tách riêng, tính tỷ lệ `age_days > 180` và chỉ FAIL nếu vượt 25%. Vì corrupted có stale ratio 5%, freshness PASS dù quality gate FAIL.

**Giới hạn:** Judge hiện là heuristic; Ragas bị skip theo mặc định. Kết quả không phải đánh giá bởi LLM judge. Hãy thêm phản ánh cá nhân về bước review và giải thích được vì sao baseline Hit Rate vẫn đạt 1.0 sau khi đã bỏ exact lookup.
