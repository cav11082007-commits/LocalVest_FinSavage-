# 🧪 Test Scenario 03: AI Fraud Shield — Multimodal NLP, pHash & Deep Learning ONNX

## Overview
Kiểm thử toàn diện Hệ thống Lá Chắn AI Chống Gian Lận (AI Fraud Shield) đa tầng, kết hợp:
1. **NLP Text Anomaly Scanner**: Phát hiện từ khóa nghi vấn, xử lý ký tự biến dạng (Leetspeak, né tránh khoảng trắng) và ngữ cảnh phủ định.
2. **Perceptual Hashing (pHash)**: Đối soát phát hiện ảnh minh chứng trùng lặp trong cơ sở dữ liệu (kể cả ảnh bị lật ngang - mirror flip).
3. **Deep Learning ONNX Classifier (`image_fraud_model.onnx`)**: Phân loại ảnh CCCD/minh chứng dự án thành 3 nhãn (`ai_generated`, `edited`, `real`).
4. **Non-Blocking Background Worker**: Chạy ngầm qua `BackgroundTasks` không gây trễ phản hồi UI.

---

## Scenario 3.1: NLP Risk Keyword Detection
- **Steps**:
  1. Đăng nhập tài khoản Project Owner.
  2. Mở trang [http://127.0.0.1:8000/submit_project.html](http://127.0.0.1:8000/submit_project.html).
  3. Nhập tiêu đề: `Quyên góp khẩn cấp cho gia đình hoàn cảnh khó khăn`.
  4. Nhập mô tả chứa các từ khóa rủi ro: `Cần tiền gấp lắm, vui lòng chuyển khoản cá nhân ngay qua tài khoản riêng, không cần xác thực giả hay mua crypto lừa đảo.`
  5. Bấm **Gửi duyệt dự án**.
- **Expected Results**:
  - API `POST /api/campaigns` tạo dự án thành công ở trạng thái `pending_review`.
  - Background task quét qua bộ từ khóa:
    - `lua dao`: +35 điểm
    - `chuyen khoan ca nhan`: +25 điểm
    - `xac thuc gia`: +30 điểm
    - `crypto`: +20 điểm
    - `gap lam`: +10 điểm
  - Tổng `fraud_score` tăng vọt lên mức tối đa `100%`.
  - Cờ `is_suspicious` bật thành `True`.

---

## Scenario 3.2: NLP Leetspeak & Evasion Bypass Detection
- **Steps**:
  1. Chủ dự án cố tình lách kiểm duyệt bằng cách viết biến dạng từ ngữ (Leetspeak, chèn dấu chấm, khoảng trắng):
     - `l.u.a  d.a.0`
     - `c h u y e n  k h o a n  c a  n h a n`
     - `cr¥pto`
  2. Gửi tạo dự án với nội dung trên.
- **Expected Results**:
  - Bộ phân tích `TextRiskAnalyzer.normalize()` và `compress()` loại bỏ toàn bộ dấu câu lạ, giải mã Leetspeak `0->o, 1->i, 3->e, 4->a, @->a, $->s`.
  - Phát hiện hành vi né tránh và gắn lý do: `"[NLP Check] ⚠️ Phát hiện từ khóa rủi ro bị né tránh bằng cách chèn khoảng trắng/ký tự lạ"`.
  - Dự án bị đánh dấu nguy cơ cao `fraud_score >= 50%`.

---

## Scenario 3.3: Contextual Negation Handling (Trừ điểm khi có từ phủ định)
- **Steps**:
  1. Tạo dự án với nội dung cam kết minh bạch có chứa từ phủ định: `Dự án tuyệt đối không lừa đảo, chúng tôi không hề nhận chuyển khoản cá nhân.`
- **Expected Results**:
  - Thuật toán `_has_negation_before()` nhận diện cửa sổ 3 từ đứng trước chứa `tuyệt đối không`, `không hề`.
  - Trọng số phạt của từ khóa được chiết khấu xuống còn `25%` (`NEGATION_DISCOUNT = 0.25`).
  - Điểm nguy cơ chỉ tăng nhẹ hợp lý, không bị phạt oan thành dự án lừa đảo.

---

## Scenario 3.4: Perceptual Hashing (pHash) Reverse Image Duplicate Detection
- **Steps**:
  1. Tải lên 1 ảnh minh chứng dự án đã từng được tải lên trong một dự án khác trước đó trên hệ thống.
  2. Gửi duyệt dự án mới.
- **Expected Results**:
  - `ImageDuplicateDetector` tính 64-bit Perceptual Hash và so sánh khoảng cách Hamming với các hash đã lưu trong DB.
  - Khoảng cách Hamming `<= 8` ➔ Xác định là ảnh trùng lặp.
  - Phạt cộng thêm `+40 điểm` vào `fraud_score`.
  - Danh sách lý do ghi nhận: `"[Project Image Check] ⚠️ 1 ảnh minh chứng nghi vấn trùng trong cơ sở dữ liệu của dự án 'proj_X'"`.

---

## Scenario 3.5: Mirror-Flipped Image Duplicate Detection (Ảnh bị lật ngang)
- **Steps**:
  1. Kẻ gian lấy ảnh từ dự án cũ, dùng phần mềm lật ngang bức ảnh (Horizontal Flip) để trốn tránh các công cụ so khớp thông thường.
  2. Tải ảnh bị lật ngang lên dự án mới và gửi duyệt.
- **Expected Results**:
  - Hệ thống tính song song cả `img_hash` gốc và `img_hash_mirrored` (qua `ImageOps.mirror()`).
  - Khoảng cách Hamming của bản lật ngang `<= 8` với ảnh gốc trong DB.
  - Gắn nhãn chi tiết: `"[Project Image Check] ⚠️ 1 ảnh minh chứng nghi vấn trùng trong cơ sở dữ liệu của dự án 'proj_X' (lật ngang)"`.
  - Điểm phạt `+40 điểm` được áp dụng chính xác.

---

## Scenario 3.6: Deep Learning ONNX Image Classifier (AI / Photoshop / Real)
- **Steps**:
  1. **Case A (Ảnh giả mạo AI)**: Tải lên ảnh CCCD hoặc ảnh hiện trường sinh bởi Midjourney/DALL-E.
  2. **Case B (Ảnh chỉnh sửa Photoshop)**: Tải lên ảnh CCCD bị cắt ghép sửa số.
  3. **Case C (Ảnh thật chính chủ)**: Tải lên ảnh chụp thực tế rõ nét.
- **Expected Results**:
  - Mô hình `image_fraud_model.onnx` phân tích ma trận điểm ảnh (Tensor `[1, 3, 224, 224]`):
    - **Case A**: Nhãn `ai_generated` ➔ Phạt `+50 điểm` (CCCD) hoặc `+40 điểm` (Dự án), lý do: `"[KYC Check] ❌ Ảnh CCCD có dấu hiệu được giả mạo bằng AI (Xác suất XX%)"`.
    - **Case B**: Nhãn `edited` ➔ Phạt `+50 điểm` (CCCD) hoặc `+20 điểm` (Dự án), lý do: `"[KYC Check] ❌ Ảnh CCCD nghi vấn bị cắt ghép/chỉnh sửa Photoshop (Xác suất XX%)"`.
    - **Case C**: Nhãn `real` ➔ Ghi nhận `"[KYC Check] ✅ Tài liệu KYC CCCD hợp lệ"`.

---

## Scenario 3.7: Non-Blocking Background Worker Execution
- **Steps**:
  1. Nhấn nút gửi dự án từ màn hình Frontend.
  2. Bấm đồng hồ đo thời gian phản hồi của request HTTP.
- **Expected Results**:
  - Request `POST /api/campaigns` phản hồi ngay lập tức với HTTP 200 trong `< 150ms`.
  - Tác vụ AI nặng (NLP + pHash + ONNX) được ủy thác cho `BackgroundTasks`, chạy ngầm mà không làm đơ/treo trình duyệt của người dùng.

---

## Scenario 3.8: Admin Fraud Inspection & One-Click Account Lock
- **Steps**:
  1. Đăng nhập tài khoản Admin `admin@gmail.com`, truy cập `admin.html`.
  2. Tại bảng kiểm duyệt dự án, tìm dự án có chỉ số gian lận cao.
  3. Xem Badge AI Fraud Score màu đỏ (ví dụ: `85%`) và danh sách các lý do AI liệt kê chi tiết.
  4. Nhấn nút **Từ chối dự án & Khóa tài khoản gian lận**.
- **Expected Results**:
  - Dự án chuyển trạng thái `rejected`.
  - Tài khoản người tạo dự án bị thiết lập `is_locked = True`.
  - Khi kẻ gian cố tình đăng nhập lại, hệ thống trả về HTTP 403: `"Tài khoản đã bị khóa do gian lận."`
