import asyncio
import sys
import os

# Thêm thư mục backend vào path
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from app.services.ai_worker import async_ai_flag_checker, FraudFlagWorker, TextRiskAnalyzer

async def test_cases():
    print("=" * 60)
    print("BẮT ĐẦU KIỂM THỬ THUẬT TOÁN AI-WORKER")
    print("=" * 60)

    # --- KỊCH BẢN 1: Văn bản sạch minh bạch ---
    res1 = await async_ai_flag_checker(
        project_id="proj_001",
        name="Thư viện cho em",
        description="Xây dựng tủ sách cộng đồng miễn phí cho trẻ em vùng ven."
    )
    print(f"\n[Case 1 - Nội dung sạch] Score: {res1['fraud_score']}% | Suspicious: {res1['is_suspicious']}")
    print(f"Lý do: {res1['reasons']}")

    # --- KỊCH BẢN 2: Từ khóa nguy hiểm bị cố tình lách luật (Leetspeak / Dấu câu) ---
    res2 = await async_ai_flag_checker(
        project_id="proj_002",
        name="Cần tiền gấp",
        description="Cần tiền g.ắ.p l.ắ.m, ch.u.y.ể.n k.h.o.ả.n c.á n.h.â.n qua crypt0 nha mọi người!"
    )
    print(f"\n[Case 2 - Lách từ khóa] Score: {res2['fraud_score']}% | Suspicious: {res2['is_suspicious']}")
    print(f"Lý do: {res2['reasons']}")

    # --- KỊCH BẢN 3: Từ khóa rủi ro đi sau từ PHỦ ĐỊNH (Tránh báo động giả) ---
    res3 = await async_ai_flag_checker(
        project_id="proj_003",
        name="Dự án minh bạch",
        description="Chúng tôi cam kết tuyệt đối không lừa đảo và không hề chuyển khoản cá nhân."
    )
    print(f"\n[Case 3 - Có từ phủ định] Score: {res3['fraud_score']}% | Suspicious: {res3['is_suspicious']}")
    print(f"Lý do: {res3['reasons']}")

if __name__ == "__main__":
    asyncio.run(test_cases())