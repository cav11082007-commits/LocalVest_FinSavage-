"""
Payment & Escrow Service API Endpoints (MoMo Webhook & Ledger)
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
import hmac
import hashlib
from app.config import settings
from app.schemas.schemas import MoMoWebhookSchema
from app.services.realtime import realtime_manager
from app.store import store

router = APIRouter(prefix="/payments", tags=["3. Payment & Escrow Service"])

@router.post("/momo-webhook")
async def momo_webhook(data: MoMoWebhookSchema):
    # 1. Bảo mật: Xác thực chữ ký HMAC-SHA256
    raw_data = f"amount={data.amount}&gatewayTxnId={data.gatewayTxnId}&projectId={data.projectId}"
    secret_key = settings.MOMO_SECRET_KEY.encode('utf-8')
    computed_sig = hmac.new(secret_key, raw_data.encode('utf-8'), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(computed_sig, data.signature):
        raise HTTPException(status_code=403, detail="Lỗi bảo mật: Chữ ký không hợp lệ (Invalid Signature)")

    # 2. Idempotency: Kiểm tra giao dịch trùng lặp
    if data.gatewayTxnId:
        exists = any(entry.get("gateway_txn_id") == data.gatewayTxnId for entry in store.ledger)
        if exists:
            # Giao dịch đã xử lý trước đó, báo OK nhưng không xử lý lại
            return {"status": "success", "message": "Giao dịch đã tồn tại, bỏ qua xử lý lặp."}

    project = next((p for p in store.projects if p["id"] == data.projectId), None)
    if not project:
        raise HTTPException(status_code=404, detail="Dự án không tồn tại")

    project["raised_amount"] += data.amount
    if project["raised_amount"] >= project["target_amount"] and project["status"] == "active":
        project["status"] = "funded"

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
    store.ledger.append(ledger_entry)

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
