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
from app.store import store

router = APIRouter(prefix="/payments", tags=["3. Payment & Escrow Service"])

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

    # 2. Idempotency: Kiểm tra giao dịch trùng lặp
    if data.gatewayTxnId:
        ledger = store.get_ledger()
        exists = any(entry.get("gateway_txn_id") == data.gatewayTxnId for entry in ledger)
        if exists:
            # Giao dịch đã xử lý trước đó, báo OK nhưng không xử lý lại
            return {"status": "success", "message": "Giao dịch đã tồn tại, bỏ qua xử lý lặp."}

    project = store.get_project_by_id(data.projectId)
    if not project:
        raise HTTPException(status_code=404, detail="Dự án không tồn tại")

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

    return {"status": "success", "message": "Ghi nhận đóng góp Escrow thành công", "ledger": ledger_entry}

@router.post("/mock-momo-pay")
async def mock_momo_pay(data: MockMoMoPaySchema):
    """
    Mock endpoint cho môi trường MVP.
    Frontend gọi API này, Backend tự sinh chữ ký HMAC bảo mật và kích hoạt luồng Webhook.
    """
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Số tiền đóng góp phải lớn hơn 0")

    # Hybrid MVP Hack: Nếu backend chưa biết dự án này (vì frontend tự mock localStorage tạo ra),
    # tự động đồng bộ dự án vào bộ nhớ backend để luồng webhook và websocket không bị lỗi 404.
    project = store.get_project_by_id(data.projectId)
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
