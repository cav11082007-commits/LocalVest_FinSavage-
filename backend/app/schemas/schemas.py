"""
LocalVest Pydantic Data Transfer Objects (DTOs)
Strict Data Schemas & API Contract Definitions
"""
import re
from pydantic import BaseModel, field_validator
from typing import List, Optional

PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*(),.?\":{}|<>_\-+=~`\[\];'])[\S]{8,}$"
)

class SendOTPSchema(BaseModel):
    identifier: Optional[str] = None
    phone_or_email: Optional[str] = None
    type: Optional[str] = None

class VerifyOTPSchema(BaseModel):
    identifier: Optional[str] = None
    phone_or_email: Optional[str] = None
    type: Optional[str] = None
    otp: Optional[str] = None
    code: Optional[str] = None
    password: Optional[str] = None

class RegisterSchema(BaseModel):
    email: str
    password: str
    full_name: str
    phone: Optional[str] = ""
    role: Optional[str] = "backer"

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        if not PASSWORD_REGEX.match(v):
            raise ValueError("Mật khẩu phải có tối thiểu 8 ký tự, gồm chữ hoa, chữ thường và ký tự đặc biệt.")
        return v

class LoginSchema(BaseModel):
    email: str
    password: str

class KYCUploadSchema(BaseModel):
    doc_type: str = "CCCD"
    doc_number: str
    front_image_url: str
    back_image_url: Optional[str] = None

class MilestoneSchema(BaseModel):
    name: str
    target_amount: float
    description: Optional[str] = ""

class CreateProjectSchema(BaseModel):
    name: str
    category: str
    description: str
    target_amount: float
    location_name: str
    lat: float = 10.7769
    lng: float = 106.7009
    milestones: List[MilestoneSchema] = []

class MoMoWebhookSchema(BaseModel):
    projectId: str
    amount: float
    backerName: Optional[str] = "Backer Ẩn Danh"
    gatewayTxnId: Optional[str] = None
    signature: str = ""

class AdminApproveSchema(BaseModel):
    projectId: str
    approve: bool

class AdminReleaseMilestoneSchema(BaseModel):
    projectId: str
    milestoneId: str
 