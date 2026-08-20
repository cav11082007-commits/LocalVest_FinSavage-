"""
Notification Service API Endpoints
"""

from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.store import store

router = APIRouter(prefix="/notifications", tags=["7. Notification Service"])


@router.get("")
def list_notifications(current_user: dict = Depends(get_current_user)):
    mine = store.get_notifications_for_user(current_user["sub"])
    unread = sum(1 for n in mine if not n["is_read"])
    return {"notifications": mine, "unreadCount": unread}


@router.post("/{notification_id}/read")
def mark_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    store.mark_notification_read(notification_id)
    return {"message": "Đã đánh dấu đã đọc"}


@router.post("/read-all")
def mark_all_read(current_user: dict = Depends(get_current_user)):
    count = store.mark_all_notifications_read(current_user["sub"])
    return {"message": f"Đã đánh dấu {count} thông báo là đã đọc"}
