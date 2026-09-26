# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** FourGuys
- **Mã Nhóm / Lớp:** `K4-L3B-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3B-DAY10-FourGuys-DataPipelineDataObservability`

---

## # Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | Đào Gia Bảo | 2A202602793 | kevindao.943@gmail.com | Corruption suite và baseline pipeline integration (`corruption.py`, `phase1.py`) | `report/2A202602793_DaoGiaBao.md` |
| 2 | Nguyễn Văn Thăng | 2A202602835 | nguyenvanthang230925@gmail.com | Data Foundation: Crossref ingestion, raw lineage và cleaning (`crossref.py`, `cleaning.py`) | `report/2A202602835_NguyenVanThang.md` |
| 3 | Đoàn Quang Thanh | 2A202602841 | respectthanh@gmail.com | RAG retrieval, vector index portability và evaluation verification (`qa.py`, `index.py`) | `report/2A202602841_DoanQuangThanh.md` |
| 4 | Đỗ Trọng Bình | 2A202602855 | dotrongbinh20012004@gmail.com | Repair orchestration và impact reporting (`corruption_flow.py`, `reporting.py`) | `report/2A202602855_DoTrongBinh.md` |

*(Nếu nhóm có 3 hoặc 5-6 thành viên, xem bảng phân công chi tiết theo vai trò trong file `CHECKPOINTS.md`.)*

---

## # Cá nhân

### ## DaoGiaBao-2A202602793
- **Vai trò:** Corruption suite và baseline pipeline integration.
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng sáu kịch bản corruption và ghi từng event vào `data/results/corruption_log.json`.
  - Tích hợp baseline pipeline trong `src/pipelines/phase1.py`.
  - Tạo lại `text_for_embedding` từ các trường đã bị biến đổi để index phản ánh dữ liệu corrupted.
- **Điều học được / Đóng góp chính:**
  - Corruption cần có log theo record và field để đối chiếu lỗi dữ liệu với quality gate và retrieval.

### ## NguyenVanThang-2A202602835
- **Vai trò:** Crossref ingestion, raw data lineage và cleaning.
- **Công việc chi tiết đã hoàn thành:**
  - Parse Crossref works thành `PaperRecord` và lưu raw response cùng parsed records.
  - Thêm fallback đọc snapshot local khi request lỗi hoặc bị rate limit.
  - Chuẩn hóa schema sạch, tính `age_days`, tạo `text_for_embedding` và khử trùng lặp theo DOI.
- **Điều học được / Đóng góp chính:**
  - Giữ raw snapshot riêng cho phép tái tạo clean data mà không dựa vào bản đã biến đổi.

### ## DoanQuangThanh-2A202602841
- **Vai trò:** Retrieval correctness, vector index portability và evaluation verification.
- **Công việc chi tiết đã hoàn thành:**
  - Bỏ exact-title lookup khỏi benchmark để retrieval Hit Rate đo kết quả tìm kiếm vector.
  - Đổi manifest Chroma sang đường dẫn tương đối và để loader dùng project configuration.
  - Xác minh answer artifacts và các metric baseline/corrupted/repaired trên cùng test set.
- **Điều học được / Đóng góp chính:**
  - Câu hỏi benchmark có title của paper không được dùng làm khóa exact lookup vì sẽ đưa ground-truth document trực tiếp vào kết quả retrieval.

### ## DoTrongBinh-2A202602855
- **Vai trò:** Repair orchestration và impact reporting.
- **Công việc chi tiết đã hoàn thành:**
  - Tích hợp corruption, evaluation và repair trong `src/pipelines/corruption_flow.py`.
  - Dựng lại repaired records từ raw snapshot rồi kiểm định và index riêng.
  - Sinh báo cáo so sánh baseline, corrupted và repaired từ metrics/quality artifacts.
- **Điều học được / Đóng góp chính:**
  - Rebuild từ raw source giữ repair độc lập với dữ liệu corrupted; quality gate và metrics xác minh recovery.
