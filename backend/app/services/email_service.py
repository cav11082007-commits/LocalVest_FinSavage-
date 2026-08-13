"""
LocalVest Email Service — Sending Real Gmail OTP Messages via SMTP & Mock Fallback
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

def send_email_otp(to_email: str, otp_code: str) -> dict:
    """Gửi email OTP trực tiếp qua Gmail SMTP hoặc lưu log mock."""
    subject = f"[LocalVest] Mã OTP xác thực của bạn là: {otp_code}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: sans-serif; background: #f4f7f6; padding: 20px;">
        <div style="max-width: 500px; margin: 0 auto; background: #fff; border-radius: 8px; padding: 20px;">
            <h2>🛡️ LocalVest OTP</h2>
            <p>Mã xác thực đăng nhập của bạn là:</p>
            <h1 style="color: #2f5496; letter-spacing: 5px;">{otp_code}</h1>
            <p>Mã có hiệu lực trong vòng 5 phút.</p>
        </div>
    </body>
    </html>
    """

    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
            msg["To"] = to_email
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, [to_email], msg.as_string())
            server.quit()
            print(f"[SUCCESS] Mail OTP sent to: {to_email}")
            return {"status": "sent", "channel": "smtp", "to": to_email}
        except Exception as e:
            print(f"[ERROR] SMTP send failed: {e}")

    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch")
    os.makedirs(log_dir, exist_ok=True)
    inbox_file = os.path.join(log_dir, "email_inbox.txt")

    with open(inbox_file, "a", encoding="utf-8") as f:
        f.write(f"=== EMAIL SENT TO: {to_email} ===\n")
        f.write(f"SUBJECT: {subject}\n")
        f.write(f"OTP CODE: {otp_code}\n")
        f.write(f"----------------------------------------\n\n")

    print(f"[EMAIL SIMULATION] OTP [{otp_code}] -> {to_email} | Log: {inbox_file}")
    return {"status": "simulated", "channel": "log_file", "to": to_email}
