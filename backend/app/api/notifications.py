"""
Notification Service API Endpoints
"""

from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.store import store

router = APIRouter(prefix="/notifications", tags=["7. Notification Service"])


def _visible_to(user: dict, n: dict) -> bool:
    """Thông báo user_id=None là thông báo chung (vd: dự án mới lên sóng) — ai cũng thấy.
    Còn lại chỉ chủ nhân (theo owner_id gán lúc notify()) mới thấy."""
    return n["user_id"] is None or n["user_id"] == user.get("sub")


@router.get("")
def list_notifications(current_user: dict = Depends(get_current_user)):
    mine = [n for n in store.notifications if _visible_to(current_user, n)]
    mine.sort(key=lambda n: n["created_at"], reverse=True)
    unread = sum(1 for n in mine if not n["is_read"])
    return {"notifications": mine, "unreadCount": unread}


@router.post("/{notification_id}/read")
def mark_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    n = next((x for x in store.notifications if x["id"] == notification_id and _visible_to(current_user, x)), None)
    if n:
        n["is_read"] = True
    return {"message": "Đã đánh dấu đã đọc"}


@router.post("/read-all")
def mark_all_read(current_user: dict = Depends(get_current_user)):
    count = 0
    for n in store.notifications:
        if _visible_to(current_user, n) and not n["is_read"]:
            n["is_read"] = True
            count += 1
    return {"message": f"Đã đánh dấu {count} thông báo là đã đọc"}
