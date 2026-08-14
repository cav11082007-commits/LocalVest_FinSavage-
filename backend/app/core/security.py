

import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from jose import jwt, JWTError
from fastapi import HTTPException, Header, Depends
from app.config import settings

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    if len(pwd_bytes) > 72:
        pwd_bytes = pwd_bytes[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        pwd_bytes = plain_password.encode('utf-8')
        if len(pwd_bytes) > 72:
            pwd_bytes = pwd_bytes[:72]
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(user_id: str, email: str, role: str) -> str:
    """Sinh JWT Access Token mã hóa thông tin user_id, email, role và thời gian hết hạn."""
    expires_delta = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.ALGORITHM)

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, str]:
    """
    Middleware giải mã và xác thực JWT Token từ Auth Header (Bearer <token>).
    Trả về 401 Unauthorized nếu thiếu token hoặc token sai/hết hạn.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Thiếu hoặc sai định dạng Auth Header (Bearer <token>)")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")

def require_role(allowed_roles: List[str]):
    """
    Dependency checker cho phân quyền RBAC dựa trên danh sách các vai trò được phép (backer, project_owner, admin).
    Trả về 403 Forbidden nếu vai trò của người dùng không nằm trong danh sách cho phép.
    """
    def role_checker(current_user: Dict[str, str] = Depends(get_current_user)):
        user_role = current_user.get("role", "backer")
        if user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Bị từ chối: Bạn không có quyền thực hiện thao tác này!")
        return current_user
    return role_checker

def require_admin(current_user: Dict[str, str] = Depends(get_current_user)):
    """
    Dependency rút gọn bảo vệ các endpoint Quản trị viên (/api/admin/*).
    Trả về 403 Forbidden nếu user.role != 'admin'.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bị từ chối: Quyền Quản trị viên mới được phép truy cập!")
    return current_user
