# BẢNG PHÂN CÔNG CÔNG VIỆC (TASK ASSIGNMENT)
**Dự án:** LocalVest-FinSavage  
**Giai đoạn:** Test & Hoàn thiện sản phẩm (Pre-launch)  
**Ngày cập nhật:** 10/08/2026  

---

## 🎯 MỤC TIÊU CHUNG
Hoàn thiện test toàn bộ hệ thống, xử lý dứt điểm các module còn dang dở (backend/frontend) dựa trên `IMPLEMENTATION_PLAN.md` và `TEST_PLAN.md`, đồng thời fix toàn bộ bugs phát hiện được nhằm đảm bảo sản phẩm vận hành mượt mà trước khi chính thức ra mắt.

---

## 👥 BẢNG PHÂN CÔNG CHI TIẾT

| Nhóm | Tên | Đầu việc cụ thể | Module liên quan | Deadline gợi ý | Ghi chú |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Core IT** | **Nam (Lead)** | - Code & Test API Webhook thanh toán (MoMo/VNPay)<br>- Xử lý logic Sổ cái Ký quỹ (Escrow)<br>- Triển khai hạ tầng (Deploy)<br>- Tổng hợp báo cáo Core IT, review code | **Payment & Escrow (Ưu tiên cao nhất)**<br>Deployment | **12/08/2026** | Tập trung tuyệt đối vào dòng tiền minh bạch. Đảm bảo bảo mật tối đa. |
| **Core IT** | **Linh** | - Hoàn thiện OTP Login, Phân quyền RBAC<br>- Cập nhật State Machine (Pending ➔ Active)<br>- Xử lý thuật toán Geofencing bản đồ 3-5km | Auth<br>Campaign<br>Location | **13/08/2026** | Đảm bảo luồng tạo dự án và hiển thị xung quanh vị trí user mượt mà. |
| **Core IT** | **Bích** | - Nâng cấp UI/UX Admin Dashboard<br>- Test Realtime WebSocket (Live Feed)<br>- Hoàn thiện hệ thống thông báo (Notification) | Admin<br>Realtime<br>Notification | **13/08/2026** | Đảm bảo tính Real-time của dòng tiền và luồng phê duyệt Admin. |
| **DS** | **Vũ (Lead)** | - Đánh giá độ chính xác tổng thể mô hình Anti-Fraud<br>- Điều chỉnh ngưỡng (fraud_score threshold)<br>- Đánh giá recommendation<br>- Tổng hợp báo cáo DS | AI-Flag Service<br>Recommendation | **12/08/2026** | Bám sát số liệu test, giảm thiểu tối đa false-positive trong AI. |
| **DS** | **Như** | - Tối ưu thuật toán NLP quét từ khóa rủi ro<br>- Tối ưu thuật toán pHash (Reverse-image) chống trùng lặp ảnh dự án | AI-Flag Service | **13/08/2026** | Chú ý các trường hợp ảnh minh chứng giả mạo trên mạng. |

---

## 📢 QUY TRÌNH BÁO CÁO & THEO DÕI TIẾN ĐỘ

1. **Kênh báo cáo:** Mọi người cập nhật tiến độ (Done, In-progress, Blocked) hàng ngày vào lúc **17:00** trên Group chat của nhóm.
2. **Quản lý chất lượng:** 
   - **Nam** phụ trách Review Code và Test chéo cho Linh & Bích trước khi Merge.
   - **Vũ** phụ trách Review Model accuracy và Data pipeline của Như.
3. **Checklist chung:** Các members chủ động tick done trên bảng Trello/Jira (nếu có) hoặc báo trực tiếp cho Lead.
4. **Deadline Tổng Thể Dự Kiến:** Toàn bộ hệ thống phải hoàn thiện không còn bug nghiêm trọng (Blocker/Critical) vào cuối ngày **14/08/2026**.

> *Đề nghị tất cả thành viên bám sát tiến độ. Chúc cả team hoàn thành xuất sắc nhiệm vụ!*
