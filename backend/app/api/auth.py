"""
Auth & User Service API Endpoints
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.schemas import RegisterSchema, LoginSchema, KYCUploadSchema
from app.core.security import create_access_token, get_current_user
from app.store import store

router = APIRouter(prefix="/auth", tags=["1. Auth & User Service"])

@router.post("/register")
def register(data: RegisterSchema):
    for u in store.users:
        if u["email"].lower() == data.email.lower():
            raise HTTPException(status_code=400, detail="Email đã tồn tại trên hệ thống")

    new_user = {
        "id": f"usr_{uuid.uuid4().hex[:8]}",
        "email": data.email,
        "full_name": data.full_name,
        "role": data.role or "backer",
        "kyc_status": "pending",
        "is_locked": False,
        "created_at": datetime.now().isoformat()
    }
    store.users.append(new_user)
    token = create_access_token(new_user["id"], new_user["email"], new_user["role"])
    return {"message": "Đăng ký thành công", "token": token, "user": new_user}

@router.post("/login")
def login(data: LoginSchema):
    user = next((u for u in store.users if u["email"].lower() == data.email.lower()), None)
    if not user:
        raise HTTPException(status_code=401, detail="Tài khoản hoặc mật khẩu không chính xác")
    if user["is_locked"]:
        raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa do gian lận")

    token = create_access_token(user["id"], user["email"], user["role"])
    return {"message": "Đăng nhập thành công", "token": token, "user": user}

@router.post("/kyc-upload")
def upload_kyc(data: KYCUploadSchema, current_user: dict = Depends(get_current_user)):
    record = {
        "id": f"kyc_{uuid.uuid4().hex[:8]}",
        "user_id": current_user["sub"],
        "doc_type": data.doc_type,
        "doc_number": data.doc_number,
        "front_image_url": data.front_image_url,
        "back_image_url": data.back_image_url,
        "status": "pending",
        "submitted_at": datetime.now().isoformat()
    }
    store.kyc_docs.append(record)
    return {"message": "Tải lên hồ sơ KYC thành công. Đang chờ Admin duyệt.", "kyc": record}
