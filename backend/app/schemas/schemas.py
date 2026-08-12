"""
LocalVest Pydantic Data Transfer Objects (DTOs)
Strict Data Schemas & API Contract Definitions
"""

from pydantic import BaseModel
from typing import List, Optional

class RegisterSchema(BaseModel):
    email: str
    password: str
    full_name: str
    role: Optional[str] = "backer"

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
