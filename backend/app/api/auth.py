import uuid
import random
import time
import re
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from app.config import settings
from app.schemas.schemas import RegisterSchema, LoginSchema, KYCUploadSchema, SendOTPSchema, VerifyOTPSchema, PASSWORD_REGEX
from app.core.security import create_access_token, get_current_user, require_admin, hash_password, verify_password
from app.services.email_service import send_email_otp
from app.services.sms_service import send_sms_otp
from app.store import store
 
RESERVED_ADMIN_EMAILS = ("admin@gmail.com", "admin@localvest.vn")
 
def _is_email(target: str) -> bool:
    """Kiểm tra target có đúng định dạng email không."""
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", target))
 
def _is_phone(target: str) -> bool:
    """Kiểm tra target có đúng định dạng SĐT VN (10 số, bắt đầu bằng 0) không."""
    return bool(re.match(r"^0\d{9}$", target))
 
router = APIRouter(prefix="/auth", tags=["1. Auth & User Service"])
 
@router.post("/send-otp")
def send_otp(data: SendOTPSchema):
    target = (data.identifier or data.phone_or_email or "").strip().lower()
    otp_type = (data.type or ("email" if _is_email(target) else "phone")).strip().lower()
 
    if not target:
        raise HTTPException(status_code=400, detail="Thiếu thông tin email hoặc số điện thoại (identifier)")
 
    # 1. Validate định dạng theo type
    if otp_type == "email" and not _is_email(target):
        raise HTTPException(status_code=400, detail="Định dạng Email không hợp lệ")
    elif otp_type == "phone" and not _is_phone(target):
        raise HTTPException(status_code=400, detail="Định dạng số điện thoại Việt Nam không hợp lệ (10 số, bắt đầu bằng 0)")
    elif not (_is_email(target) or _is_phone(target)):
        raise HTTPException(status_code=400, detail="Định dạng Email hoặc số điện thoại không hợp lệ")
 
    # 1.5. Chặn ngay tại đây nếu email/SĐT chưa từng đăng ký — không gửi OTP,
    # tránh người dùng đi hết bước nhập OTP rồi mới bị chặn ở /verify-otp.
    # (send-otp trong hệ thống này chỉ dùng cho luồng ĐĂNG NHẬP, không dùng để đăng ký mới.)
    if not store.find_user_by_identifier(target):
        raise HTTPException(
            status_code=404,
            detail="Email/Số điện thoại này chưa được đăng ký. Vui lòng tạo tài khoản trước khi đăng nhập."
        )
 
    now = time.time()
    record = store.otp_store.get(target)
 
    # 2. Kiểm tra nếu bị khóa 15 phút do nhập sai 5 lần
    if isinstance(record, dict) and record.get("locked_until", 0) > now:
        remaining_mins = int((record["locked_until"] - now) / 60) + 1
        raise HTTPException(
            status_code=401,
            detail=f"Số lần nhập sai OTP vượt quá 5 lần. Tạm khóa xác thực {remaining_mins} phút!"
        )
 
    # 3. Rate-limiting: Tối đa 5 lần gửi / phút cho cùng 1 identifier
    history = []
    if isinstance(record, dict):
        history = [t for t in record.get("send_history", []) if now - t < 60]
        if len(history) >= 5:
            raise HTTPException(
                status_code=429,
                detail="Bạn đã yêu cầu gửi OTP quá 5 lần trong 1 phút. Vui lòng thử lại sau!"
            )
 
    # 4. Sinh mã OTP 6 số ngẫu nhiên (hoặc '000000' nếu ENV=test)
    if getattr(settings, "ENV", "dev") == "test":
        otp_code = "000000"
    else:
        otp_code = f"{random.randint(100000, 999999)}"
 
    # 5. Lưu vào cache in-memory (TTL 5 phút = 300s)
    history.append(now)
    store.otp_store[target] = {
        "otp": otp_code,
        "code": otp_code,
        "type": otp_type,
        "expires_at": now + 300,
        "attempts": 0,
        "send_history": history,
        "locked_until": 0
    }
 
    # 6. Console Print Log dạng [MOCK-OTP]
    print(f"[MOCK-OTP] Gửi tới <{target}>: {otp_code}")
 
    if otp_type == "email":
        send_email_otp(target, otp_code)
    else:
        send_sms_otp(target, otp_code)
 
    # 7. Response JSON chuẩn API contract
    response = {
        "status": "success",
        "message": "Đã tạo mã OTP thành công",
        "identifier": target,
        "target": target,
        "sent_via": otp_type,
    }
    if settings.ENV != "prod":
        response["otp"] = otp_code
        response["mock_otp"] = otp_code
    return response
 
@router.post("/verify-otp")
def verify_otp(data: VerifyOTPSchema):
    target = (data.identifier or data.phone_or_email or "").strip().lower()
    input_otp = (data.otp or data.code or "").strip()
    now = time.time()
 
    if not target or not input_otp:
        raise HTTPException(status_code=400, detail="Thiếu identifier hoặc mã OTP")
 
    record = store.otp_store.get(target)
 
    if isinstance(record, str):
        record = {"otp": record, "code": record, "expires_at": now + 300, "attempts": 0, "locked_until": 0}
 
    if not record:
        raise HTTPException(status_code=400, detail="Chưa có mã OTP nào được gửi đến địa chỉ/SĐT này")
 
    # 1. Kiểm tra tạm khóa 15 phút
    if record.get("locked_until", 0) > now:
        remaining_mins = int((record["locked_until"] - now) / 60) + 1
        raise HTTPException(
            status_code=401,
            detail=f"Tài khoản đang bị tạm khóa xác thực OTP do nhập sai quá 5 lần. Vui lòng thử lại sau {remaining_mins} phút!"
        )
 
    # 2. Kiểm tra hết hạn (> 5 phút)
    if record.get("expires_at", 0) < now:
        raise HTTPException(
            status_code=400,
            detail="Mã OTP đã hết hạn (quá 5 phút). Vui lòng yêu cầu gửi lại mã mới!"
        )
 
    correct_otp = record.get("otp") or record.get("code") or ""
    is_valid = (input_otp == correct_otp) or (input_otp == "000000" and getattr(settings, "ENV", "dev") == "test")
 
    # 3. Kiểm tra sai mã OTP -> Tăng attempts
    if not is_valid:
        record["attempts"] = record.get("attempts", 0) + 1
        if record["attempts"] >= 5:
            record["locked_until"] = now + 900  # Khóa 15 phút
            store.otp_store[target] = record
            raise HTTPException(
                status_code=401,
                detail="Bạn đã nhập sai mã OTP quá 5 lần liên tiếp. Khóa tạm thời 15 phút!"
            )
        store.otp_store[target] = record
        remaining = 5 - record["attempts"]
        raise HTTPException(
            status_code=401,
            detail=f"Mã OTP không chính xác. Còn {remaining} lần thử!"
        )
 
    # 4. Nhập đúng -> Xóa record trong otp_store
    del store.otp_store[target]
 
    # 5. Lấy User trong Database/Store — KHÔNG tự tạo tài khoản mới qua OTP nữa.
    # find_user_by_identifier nhận diện đúng user kể cả khi đăng nhập bằng email phụ
    # (alt_emails) — ví dụ admin@gmail.com trỏ về cùng 1 tài khoản với admin@localvest.vn.
    user = store.find_user_by_identifier(target)
 
    if not user:
        # Email/SĐT chưa từng đăng ký -> từ chối thẳng, không tạo tài khoản "ma".
        # Người dùng phải đăng ký qua /register (email) trước khi dùng OTP để đăng nhập.
        raise HTTPException(
            status_code=404,
            detail="Email/Số điện thoại này chưa được đăng ký. Vui lòng tạo tài khoản trước khi đăng nhập."
        )
 
    # 5.5. Xác thực thêm mật khẩu (2 lớp: OTP + Password) — CHỈ áp dụng cho đăng nhập
    # bằng EMAIL. Đăng nhập bằng SĐT chỉ cần đúng mã OTP (SMS) là đủ, không yêu cầu
    # nhập thêm mật khẩu — vì SĐT đã đăng ký thì OTP gửi tới SĐT đó tự nó là bằng
    # chứng sở hữu, không cần lớp xác thực thứ hai.
    otp_type = record.get("type") or ("email" if _is_email(target) else "phone")
    is_email_login = otp_type == "email" or _is_email(target)
 
    if is_email_login and user.get("password_hash"):
        if not data.password or not verify_password(data.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Mật khẩu không chính xác")
 
    # 6. Sinh và trả về JWT Access Token
    token = create_access_token(user["id"], user["email"], user["role"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
        "token": token,
        "message": "Xác thực OTP thành công",
        "verified": True
    }
 
@router.post("/register")
def register(data: RegisterSchema):
    email_clean = data.email.strip().lower()
    if store.find_user_by_identifier(email_clean):
        raise HTTPException(status_code=400, detail="Email đã tồn tại trên hệ thống")
 
    phone_clean = (data.phone or "").strip()
    if phone_clean and store.find_user_by_identifier(phone_clean):
        raise HTTPException(status_code=400, detail="Số điện thoại đã tồn tại trên hệ thống")
 
    if email_clean in RESERVED_ADMIN_EMAILS:
        raise HTTPException(status_code=400, detail="Email này được bảo lưu cho tài khoản Admin, không thể đăng ký mới.")
 
    role = data.role or "backer"
 
    alt_emails = []
    if phone_clean:
        alt_emails.append(phone_clean)

    new_user = {
        "id": f"usr_{uuid.uuid4().hex[:8]}",
        "email": email_clean,
        "full_name": data.full_name,
        "phone": phone_clean,
        "alt_emails": alt_emails,
        "password_hash": hash_password(data.password),
        "role": role,
        "kyc_status": "pending",
        "is_locked": False,
        "created_at": datetime.now().isoformat()
    }
    store.create_user(new_user)
    token = create_access_token(new_user["id"], new_user["email"], new_user["role"])
    safe_user = {k: v for k, v in new_user.items() if k != "password_hash"}
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": safe_user,
        "token": token,
        "message": "Đăng ký thành công"
    }
 
@router.post("/login")
def login(data: LoginSchema):
    """Login Function (Format,.... )"""
    target = data.email.strip().lower()
    user = store.find_user_by_identifier(target)
 
    if not user or not verify_password(data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Tài khoản hoặc mật khẩu không chính xác")
    if user.get("is_locked", False):
        raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa do gian lận")
 
    token = create_access_token(user["id"], user["email"], user["role"])
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": safe_user,
        "token": token,
        "message": "Đăng nhập thành công"
    }
 
@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    user = store.get_user_by_id(current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    safe_user = {k: v for k, v in user.items() if k != "password_hash"}
    return {"user": safe_user}

@router.post("/kyc-upload")
def upload_kyc(data: KYCUploadSchema, current_user: dict = Depends(get_current_user)):
    record = {
        "id": f"kyc_{uuid.uuid4().hex[:8]}",
        "user_id": current_user["sub"],
        "doc_type": data.doc_type,
                "front_image_url": data.front_image_url,
        "back_image_url": data.back_image_url,
        "status": "pending",
        "submitted_at": datetime.now().isoformat()
    }
    store.create_kyc_doc(record)
    return {"message": "Tải lên hồ sơ KYC thành công. Đang chờ Admin duyệt.", "kyc": record}
 