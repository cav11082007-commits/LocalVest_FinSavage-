# 🧪 Test Scenario 05: Realtime Live Feed WebSocket & Event Broadcasting

## Overview
Kiểm thử kênh truyền dữ liệu thời gian thực hai chiều WebSocket (`ws://127.0.0.1:8000/ws/live-feed`), đảm bảo toàn bộ các sự kiện tài chính, phê duyệt dự án, giải ngân và thông báo hệ thống được truyền phát tức thời tới tất cả client đang kết nối mà **không cần bấm F5 / Refresh**.

---

## Scenario 5.1: WebSocket Connection Lifecycle & Heartbeat
- **Steps**:
  1. Mở kết nối WebSocket từ trình duyệt hoặc client test đến `ws://127.0.0.1:8000/ws/live-feed`.
  2. Gửi chuỗi text ping giữ kết nối.
- **Expected Results**:
  - Máy chủ Backend chấp nhận kết nối (HTTP 101 Switching Protocols).
  - Trình quản lý `realtime_manager` thêm WebSocket vào danh sách kết nối hoạt động (`active_connections`).
  - Khi đóng tab, máy chủ tự động hủy đăng ký (Disconnect) an toàn mà không gây rò rỉ bộ nhớ (Memory Leak).

---

## Scenario 5.2: `NEW_TRANSACTION` Live Push on Backer Contribution
- **Steps**:
  1. Mở 2 tab trình duyệt song song:
     - **Tab 1**: Mở trang Sổ cái dòng tiền `http://127.0.0.1:8000/dashboard.html`.
     - **Tab 2**: Mở trang Đóng góp `http://127.0.0.1:8000/checkout.html?id=proj_1`.
  2. Tại Tab 2 thực hiện đóng góp `100.000đ` qua MoMo Sandbox.
- **Expected Results**:
  - Backend phát sự kiện `NEW_TRANSACTION` qua WebSocket với payload:
    ```json
    {
      "event": "NEW_TRANSACTION",
      "data": {
        "projectId": "proj_1",
        "projectName": "Phòng học miễn phí cho trẻ em xóm trọ",
        "backerName": "Nguyễn Văn An",
        "amount": 100000,
        "raisedTotal": 21100000,
        "targetTotal": 30000000
      }
    }
    ```
  - Tại Tab 1, hàng giao dịch mới lập tức xuất hiện kèm hiệu ứng nhấp nháy (Flash Animation).
  - Biểu đồ dòng tiền Chart.js và Tổng số dư quỹ Escrow tự động cập nhật ngay tức thì.

---

## Scenario 5.3: `MILESTONE_RELEASED` Event on Admin Disbursement
- **Steps**:
  1. Mở trang chi tiết dự án `http://127.0.0.1:8000/project.html?id=proj_1` trên màn hình Backer.
  2. Trên cửa sổ Quản trị Admin, thực hiện duyệt giải ngân mốc `Sửa chữa phòng học`.
- **Expected Results**:
  - WebSocket phát broadcast sự kiện `MILESTONE_RELEASED`:
    ```json
    {
      "event": "MILESTONE_RELEASED",
      "data": {
        "projectId": "proj_1",
        "projectName": "Phòng học miễn phí cho trẻ em xóm trọ",
        "milestoneName": "Sửa chữa phòng học, lắp bàn ghế",
        "amount": 12000000
      }
    }
    ```
  - Màn hình người dùng tự động chuyển trạng thái mốc sang Badge xanh **"Đã giải ngân"** mà không cần tải lại trang.

---

## Scenario 5.4: `PROJECT_APPROVED` / `PROJECT_REJECTED` Moderation Events
- **Steps**:
  1. Chủ dự án đang ở trang cá nhân hoặc xem danh sách dự án.
  2. Admin thực hiện Duyệt hoặc Từ chối một dự án đang `pending_review`.
- **Expected Results**:
  - Backend phát sự kiện `PROJECT_APPROVED` hoặc `PROJECT_REJECTED`.
  - Giao diện danh sách dự án của toàn bộ người dùng lập tức xuất hiện dự án mới được duyệt.

---

## Scenario 5.5: `NOTIFICATION` Real-Time Push to Notification Center
- **Steps**:
  1. User đang đăng nhập trên hệ thống.
  2. Có người ủng hộ dự án của user hoặc Admin giải ngân một mốc của user.
- **Expected Results**:
  - Sự kiện `NOTIFICATION` được đẩy trực tiếp qua WebSocket:
    ```json
    {
      "event": "NOTIFICATION",
      "data": {
        "id": "ntf_xxxxx",
        "user_id": "usr_owner",
        "title": "Có khoản đóng góp mới",
        "message": "Trần Văn An vừa đóng góp 200,000đ...",
        "type": "donation",
        "is_read": false
      }
    }
    ```
  - Icon Chuông thông báo trên Header tăng số đếm chưa đọc `+1` kèm hiệu ứng rung.
