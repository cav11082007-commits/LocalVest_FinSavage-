# 🧪 Test Scenario 06: Notification Service & Dual-Channel Alert Hub

## Overview
Kiểm thử Hệ thống Thông báo (Notification Service) đa kênh kết hợp: Lưu trữ bền vững trong cơ sở dữ liệu (SQLite Persistent Storage) và Đẩy tức thời qua WebSocket (Realtime Push), hỗ trợ quản lý trạng thái đã đọc/chưa đọc và phân loại thông báo theo nghiệp vụ (`donation`, `approval`, `milestone`, `info`).

---

## Scenario 6.1: List User Notifications & Unread Badge Counter
- **Preconditions**: Người dùng đã đăng nhập và sở hữu ít nhất 1 dự án nhận được đóng góp.
- **Steps**:
  1. Gửi request `GET /api/notifications` kèm Header `Authorization: Bearer <token>`.
- **Expected Results**:
  - API trả về HTTP 200 với cấu trúc JSON:
    ```json
    {
      "notifications": [
        {
          "id": "ntf_abc12345",
          "user_id": "usr_demo",
          "title": "Có khoản đóng góp mới",
          "message": "Trần Văn An vừa đóng góp 200,000đ cho dự án 'Phòng học miễn phí'...",
          "type": "donation",
          "is_read": false,
          "created_at": "2026-08-20T19:30:00"
        }
      ],
      "unreadCount": 1
    }
    ```
  - Giá trị `unreadCount` phản ánh chính xác số lượng bản ghi có `is_read = false`.
  - Icon Chuông thông báo trên Header hiển thị Badge đỏ với số đếm tương ứng.

---

## Scenario 6.2: Mark Specific Notification as Read
- **Steps**:
  1. Người dùng bấm vào một thông báo cụ thể trong danh sách.
  2. Giao diện gọi API `POST /api/notifications/{notification_id}/read`.
- **Expected Results**:
  - API trả về `{"message": "Đã đánh dấu đã đọc"}`.
  - Cột `is_read` của bản ghi trong bảng `notifications` được cập nhật thành `1` (True).
  - Giá trị `unreadCount` giảm đi `1`.
  - Item thông báo đổi màu nền sang trạng thái đã đọc.

---

## Scenario 6.3: Mark All Notifications as Read (Đánh dấu tất cả đã đọc)
- **Steps**:
  1. Người dùng bấm nút **"Đánh dấu tất cả đã đọc"** trên Trung tâm thông báo.
  2. Giao diện gửi request `POST /api/notifications/read-all`.
- **Expected Results**:
  - API thực thi cập nhật hàng loạt và phản hồi: `{"message": "Đã đánh dấu X thông báo là đã đọc"}`.
  - Toàn bộ thông báo của người dùng này chuyển sang `is_read = true`.
  - `unreadCount` trở về `0` và Badge đỏ trên icon Chuông biến mất.

---

## Scenario 6.4: Automatic Event Trigger & Dual-Channel Delivery
- **Steps**:
  1. Backer thực hiện quyên góp `200.000đ` cho dự án của Chủ dự án A.
- **Expected Results**:
  - **Kênh 1 (Persistent DB)**: Hàm `notify()` tự động tạo bản ghi trong bảng `notifications` với `user_id = A`, `type = 'donation'`.
  - **Kênh 2 (Realtime WebSocket)**: Phát đồng thời qua `ws://127.0.0.1:8000/ws/live-feed` sự kiện `NOTIFICATION`.
  - Chủ dự án A nhận được Popup thông báo ngay lập tức nếu đang online, và vẫn xem lại được lịch sử thông báo khi đăng nhập vào ngày hôm sau.
