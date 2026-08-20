"""
Payment & Escrow Service API Endpoints (MoMo Webhook & Ledger)
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
import hmac
import hashlib
from app.config import settings
from app.schemas.schemas import MoMoWebhookSchema, MockMoMoPaySchema
from app.services.realtime import realtime_manager
from app.services.notifications import notify
from app.store import store

router = APIRouter(prefix="/payments", tags=["3. Payment & Escrow Service"])

# (Đã xoá GET /ledger/{project_id} — bản cũ của mình, dùng store.ledger không còn tồn
# tại sau khi store.py chuyển hẳn sang SQLite thật của develop. Không còn ai gọi tới
# endpoint này nữa: dashboard.html giờ dùng LV.getLedger() -> GET
# /api/campaigns/{id}/ledger (đã có sẵn, dùng đúng store.get_ledger() thật) — giữ 1
# đường lấy sổ cái duy nhất thay vì để 2 endpoint trùng việc, 1 cái còn hỏng.)

@router.post("/momo-webhook")
async def momo_webhook(data: MoMoWebhookSchema):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Số tiền đóng góp phải lớn hơn 0")

    # 1. Bảo mật: Xác thực chữ ký HMAC-SHA256
    raw_data = f"amount={data.amount}&gatewayTxnId={data.gatewayTxnId}&projectId={data.projectId}"
    secret_key = settings.MOMO_SECRET_KEY.encode('utf-8')
    computed_sig = hmac.new(secret_key, raw_data.encode('utf-8'), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(computed_sig, data.signature):
        raise HTTPException(status_code=403, detail="Lỗi bảo mật: Chữ ký không hợp lệ (Invalid Signature)")

    # 2. Idempotency: Kiểm tra giao dịch trùng lặp O(1)
    if data.gatewayTxnId:
        if store.check_txn_exists(data.gatewayTxnId):
            # Giao dịch đã xử lý trước đó, báo OK nhưng không xử lý lại
            return {"status": "success", "message": "Giao dịch đã tồn tại, bỏ qua xử lý lặp."}

    project = store.get_project_by_id(data.projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Dự án không tồn tại")
        
    if project.get("status") in ["funded", "completed"]:
        raise HTTPException(status_code=400, detail="Dự án này đã đạt đủ mục tiêu tài chính. Hệ thống tự động khóa sổ, không nhận thêm Quyên góp.")

    store.update_project_raised_amount(data.projectId, data.amount)
    # the method update_project_raised_amount also handles status update to funded if target reached.

    ledger_entry = {
        "id": f"tx_{uuid.uuid4().hex[:8]}",
        "project_id": data.projectId,
        "user_name": data.backerName or "Nhà tài trợ ẩn danh",
        "amount": data.amount,
        "type": "escrow_deposit",
        "gateway": "momo",
        "gateway_txn_id": data.gatewayTxnId or f"MOMO_{int(datetime.now().timestamp())}",
        "description": f"+{data.amount:,.0f}đ từ {data.backerName} (Ký quỹ Escrow)",
        "created_at": datetime.now().isoformat()
    }
    store.add_ledger_entry(ledger_entry)

    # Push to Realtime Live Feed WebSocket
    await realtime_manager.broadcast("NEW_TRANSACTION", {
        "projectId": project["id"],
        "projectName": project["name"],
        "backerName": ledger_entry["user_name"],
        "amount": data.amount,
        "raisedTotal": project["raised_amount"],
        "targetTotal": project["target_amount"]
    })
    await notify(
        user_id=project.get("owner_id"),
        title="Có khoản đóng góp mới",
        message=f'{ledger_entry["user_name"]} vừa đóng góp {data.amount:,.0f}đ cho dự án "{project["name"]}".',
        n_type="donation",
    )

    return {"status": "success", "message": "Ghi nhận đóng góp Escrow thành công", "ledger": ledger_entry}

@router.post("/mock-momo-pay")
async def mock_momo_pay(data: MockMoMoPaySchema):
    """
    Mock endpoint cho môi trường MVP.
    Frontend gọi API này, Backend tự sinh chữ ký HMAC bảo mật và kích hoạt luồng Webhook.
    """
    if getattr(settings, "ENV", "dev") == "prod":
        raise HTTPException(status_code=403, detail="Endpoint mock bị khóa trên môi trường Production")

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Số tiền đóng góp phải lớn hơn 0")

    # Hybrid MVP Hack: Nếu backend chưa biết dự án này (vì frontend tự mock localStorage tạo ra),
    # tự động đồng bộ dự án vào bộ nhớ backend để luồng webhook và websocket không bị lỗi 404.
    project = store.get_project_by_id(data.projectId)
    if project and project.get("status") in ["funded", "completed"]:
        raise HTTPException(status_code=400, detail="Dự án này đã đạt đủ mục tiêu tài chính. Hệ thống tự động khóa sổ, không nhận thêm Quyên góp.")
        
    if not project:
        store.create_project({
            "id": data.projectId,
            "owner_id": "usr_demo",
            "name": data.projectName or f"Dự án {data.projectId}",
            "category": "Khác",
            "description": "Dự án giả lập",
            "location_name": "Không xác định",
            "lat": 0,
            "lng": 0,
            "creator_name": "System",
            "target_amount": data.targetAmount or 100000000.0,
            "raised_amount": data.currentRaised or 0.0,
            "status": "active"
        })

    gateway_txn_id = f"MOCK_MOMO_{int(datetime.now().timestamp())}"
    raw_data = f"amount={data.amount}&gatewayTxnId={gateway_txn_id}&projectId={data.projectId}"
    secret_key = settings.MOMO_SECRET_KEY.encode('utf-8')
    computed_sig = hmac.new(secret_key, raw_data.encode('utf-8'), hashlib.sha256).hexdigest()

    webhook_data = MoMoWebhookSchema(
        projectId=data.projectId,
        amount=data.amount,
        backerName=data.backerName,
        gatewayTxnId=gateway_txn_id,
        signature=computed_sig
    )
    
    # Kích hoạt luồng webhook thật
    return await momo_webhook(webhook_data)

from pydantic import BaseModel
class DisburseRequest(BaseModel):
    milestone_index: int

@router.post("/disburse/{project_id}")
async def disburse_milestone(project_id: str, payload: DisburseRequest):
    project = store.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Không tìm thấy dự án")
        
    milestones = project.get("milestones", [])
    if payload.milestone_index >= len(milestones):
        raise HTTPException(status_code=400, detail="Mốc giải ngân không tồn tại")
        
    m = milestones[payload.milestone_index]
    if m.get("status") == "released":
        raise HTTPException(status_code=400, detail="Mốc này đã được giải ngân")
        
    import random
    import json
    from app.services.disbursement_auditor import evaluate_disbursement
    
    target = project.get("target_amount", 1)
    amt = float(m.get("target_amount") or m.get("amount") or 0)
    raised = float(project.get("raised_amount") or 0)
    if raised < amt:
        raise HTTPException(status_code=400, detail=f"Số dư quỹ Escrow không đủ! (Quỹ hiện có: {raised:,.0f}đ, Cần rút: {amt:,.0f}đ)")
        
    ratio = min(amt / target, 1.0) if target > 0 else 0.0
    
    # AI trigger config: Ratio > 0.4 triggers block
    if ratio > 0.4:
        features = [99.99] # pass invalid length to force fallback 99.99
    else:
        features = [0.05, 0.02] + [random.uniform(0,1) for _ in range(9)]
                
    ai_report_json = evaluate_disbursement(project_id, features)
    ai_report = json.loads(ai_report_json)
    
    risk_score = ai_report.get("risk_score_percent", 0.0)
    
    if risk_score >= 50.0:
        flag = store.get_ai_flag(project_id)
        if flag:
            flag["score"] = min(100, flag.get("score", 0) + 30)
            reasons = flag.get("reason", "")
            if "Bị AI chặn giải ngân" not in reasons:
                flag["reason"] = reasons + " | Bị AI chặn giải ngân"
            store.set_ai_flag(flag)
        raise HTTPException(status_code=403, detail=ai_report)
        
    import uuid
    store.update_milestone_status(m["id"], "released")
    
    entry = {
        "id": f"tx_{uuid.uuid4().hex[:8]}",
        "project_id": project_id,
        "amount": amt,
        "type": "milestone_release",
        "description": f"Giải ngân mốc '{m.get('name')}'"
    }
    store.add_ledger_entry(entry)
    
    return {"status": "success", "ai_report": ai_report}
