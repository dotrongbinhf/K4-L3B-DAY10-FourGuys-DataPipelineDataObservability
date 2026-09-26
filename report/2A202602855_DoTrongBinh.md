# Individual Report — Đỗ Trọng Bình (2A202602855)

> Bản nháp này tổng hợp từ Git history và artifacts. Thành viên đứng tên cần rà soát, bổ sung trải nghiệm cá nhân và xác nhận nội dung trước khi nộp.

## Vai trò và bằng chứng

**Vai trò:** Repair orchestration, comparison reporting và kết quả pipeline. Commit tiêu biểu: `d3d63c6` (`feat: step 8`).

| Phần việc | File/artifact | Kết quả |
|---|---|---|
| Điều phối corruption → evaluation → repair → comparison | `src/pipelines/corruption_flow.py` | Chạy cùng test set cho corrupted/repaired và báo cáo ba trạng thái |
| Rebuild dữ liệu từ raw snapshot | `src/pipelines/corruption_flow.py` | Repair không dựa trên bản corrupted; quality/freshness gate phải pass trước khi index repaired |
| Xuất kết quả | `src/observability/reporting.py`, `data/reports/corruption_report.md` | Bảng baseline/corrupted/repaired cùng tác động metrics |
| Bàn giao artifacts | `data/clean/`, `data/embeddings/`, `data/quality/`, `data/results/`, `data/chroma/` | Có corrupted và repaired data, quality reports, answers và metrics |

## Kết quả thực tế

Pipeline sửa tạo 24 rows từ raw; corrupted có 20 rows. Baseline → corrupted → repaired: retrieval hit rate 1.000 → 0.500 → 1.000; token F1 0.900 → 0.621 → 0.900; judge accuracy 0.900 → 0.600 → 0.900. Quality gate PASS → FAIL → PASS. Freshness PASS ở cả ba state; stale ratio của corrupted là 5%, thấp hơn ngưỡng 25%.

## Repair và reproducibility

Repair khởi đầu từ `data/raw/crossref_records.json`, chạy lại cleaning, quality checks và tạo collection repaired mới. Ba evaluation dùng `data/eval/test_set.json`; kiểm tra answer artifacts xác nhận question, ground truth và document IDs giống nhau. Báo cáo được sinh từ metrics/quality objects của lần chạy thay vì nhập tay.

## Điểm cần trình bày

Trong demo, chỉ ra sự khác nhau giữa gate chất lượng và freshness SLA: duplicate/blank summary khiến quality FAIL, còn tỷ lệ stale 5% chưa đủ làm freshness FAIL. Giải thích pipeline vẫn index corrupted dataset để đo tác động thực nghiệm, trong khi repaired data chỉ được index sau khi gate pass.

**Lưu ý cá nhân:** Bổ sung các lỗi orchestration cụ thể bạn trực tiếp xử lý và cách bạn tự xác minh idempotence trước khi nộp.
