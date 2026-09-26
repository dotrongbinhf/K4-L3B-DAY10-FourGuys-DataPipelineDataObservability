# K4-L3B-Day10 — Data Pipeline & Data Observability for RAG

> **Hình thức:** Teamwork | **Thời lượng:** 240 phút  
> **Lịch học (Lớp B - Ca Sáng):** Thứ 7 (26/09/2026) 09:00 – 13:00  
> ⏰ **Hạn nộp LMS:** 23:59:59 cùng ngày

---

## 🧭 Đọc gì, theo thứ tự nào?

| # | Tài liệu | Mô tả |
|:---:|---|---|
| 1️⃣ | **Codelab trên VLearn LMS** | Hướng dẫn từng bước + nộp bài (mở trên trình duyệt) |
| 2️⃣ | [CHECKPOINTS.md](docs/CHECKPOINTS.md) | Phân bổ thời gian 240 phút & deliverables từng mốc |
| 3️⃣ | [RUBRIC.md](docs/RUBRIC.md) | Tiêu chí chấm điểm (100 chuẩn + 10 bonus) |
| 4️⃣ | [SUBMISSION.md](docs/SUBMISSION.md) | Nội quy, deadline, bảo mật & checklist nộp bài |
| 5️⃣ | [TEAM.md](docs/TEAM.md) | Thành viên, phân công và checklist |

---

## Repo có gì?

- `data/raw/` — Crossref response và parsed records để tái chạy offline
- `src/` — Ingestion, cleaning, Great Expectations 1.x quality gate, retrieval, evaluation và repair flow
- `data/` — Clean/corrupted/repaired datasets, ChromaDB, metrics, quality reports và comparison report
- `script/` — Entrypoints: `run_phase1.py`, `run_corruption_flow.py`
- `docs/DEMO_GUIDE.md` — Kịch bản demo và câu hỏi phản biện gợi ý
- `report/` — Báo cáo nhóm và bản nháp báo cáo cá nhân cần từng thành viên tự rà soát

## Chạy pipeline

```bash
uv sync
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

## Việc nghiệm thu còn lại

Rà soát và cá nhân hóa các báo cáo thành viên, xác nhận mọi người xuất hiện trong GitHub Insights → Contributors sau lần push cuối, trình diễn/Q&A trực tiếp và mỗi cá nhân tự nộp repository link lên VLearn LMS. Xem [kịch bản demo](docs/DEMO_GUIDE.md) và [checklist submission](docs/SUBMISSION.md).
