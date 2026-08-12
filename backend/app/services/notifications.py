"""
LocalVest Notification Service
Khác với toast (frontend/js/app.js LV.toast) chỉ hiện vài giây rồi biến mất, thông báo ở
đây được LƯU TRỮ trong store — người dùng có thể quay lại xem sau, đánh dấu đã đọc.
Dùng lại đúng ConnectionManager của realtime.py để đẩy tức thời (không phải đánh đổi
giữa "lưu trữ" và "tức thời", làm cả hai cùng lúc bằng một hạ tầng duy nhất).
"""

import uuid
from datetime import datetime
from typing import Optional
from app.store import store
from app.services.realtime import realtime_manager


async def notify(user_id: Optional[str], title: str, message: str, n_type: str = "info") -> dict:
    """Tạo một thông báo lưu trữ được và phát ngay qua WebSocket.
    user_id=None nghĩa là thông báo chung cho mọi người (vd: có dự án mới lên sóng)."""
    n = {
        "id": f"ntf_{uuid.uuid4().hex[:8]}",
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": n_type,
        "is_read": False,
        "created_at": datetime.now().isoformat(),
    }
    store.notifications.append(n)
    await realtime_manager.broadcast("NOTIFICATION", n)
    return n
