"""
SMS OTP Service — Mock Gateway cho giai đoạn dev/test (Task 1 MVP).
"""
import os

def send_sms_otp(phone: str, otp_code: str) -> dict:
    """Gửi SMS OTP giả lập (Mock Gateway)."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch")
    os.makedirs(log_dir, exist_ok=True)
    sms_file = os.path.join(log_dir, "sms_outbox.txt")

    with open(sms_file, "a", encoding="utf-8") as f:
        f.write(f"=== MOCK SMS TO: {phone} ===\n")
        f.write(f"BODY: Ma OTP dang nhap LocalVest cua ban la: {otp_code}. Co hieu luc trong 5 phut.\n")
        f.write(f"----------------------------------------\n\n")

    print(f"[MOCK-OTP] Gửi tới <{phone}>: {otp_code}")
    return {"status": "simulated", "channel": "sms_mock", "to": phone, "otp": otp_code}
