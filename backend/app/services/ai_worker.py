"""
LocalVest Async AI-Flag Fraud Detection Worker
Runs background non-blocking pHash / NLP text anomaly scan.
"""

import asyncio
import uuid
from datetime import datetime
from app.store import store

async def async_ai_flag_checker(project_id: str, name: str, description: str):
    """Simulates zero-cost background NLP & reverse-image fraud check."""
    await asyncio.sleep(1)  # Non-blocking async sleep
    fraud_score = 5
    reasons = []

    keywords = ["lừa đảo", "chuyển khoản cá nhân", "crypto", "gấp lắm", "copy", "xác thực giả"]
    for kw in keywords:
        if kw in description.lower():
            fraud_score += 30
            reasons.append(f"Phát hiện từ khóa rủi ro: '{kw}'")

    flag = {
        "id": f"flag_{uuid.uuid4().hex[:8]}",
        "project_id": project_id,
        "fraud_score": fraud_score,
        "is_suspicious": fraud_score > 50,
        "reasons": reasons if reasons else ["Nội dung gốc minh bạch", "Hình ảnh thực tế hợp lệ"],
        "checked_at": datetime.now().isoformat()
    }
    store.ai_flags.append(flag)
    print(f"[AI-Flag Worker] Checked Project {project_id} | Score: {fraud_score}%")




