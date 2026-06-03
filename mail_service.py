"""
mail_service.py — OTP generation and email delivery via Gmail SMTP
"""
from flask_mail import Mail, Message
import random


def generate_otp() -> str:
    """Generate a random 6-digit OTP string."""
    return str(random.randint(100000, 999999))


def send_otp_email(app, mail: Mail, to_email: str, otp: str, student_name: str = "Student") -> None:
    """Send OTP to student's email using Flask-Mail."""
    with app.app_context():
        msg = Message(
            subject="🗳️ Your SWC Election Login OTP",
            sender=app.config["MAIL_USERNAME"],
            recipients=[to_email],
        )
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;
                    border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
          <div style="background: #1a237e; padding: 20px; text-align: center;">
            <h2 style="color: #ffd600; margin: 0;">🏛️ SWC Election Platform</h2>
            <p style="color: #ffffff; margin: 4px 0 0;">Student Welfare Council</p>
          </div>
          <div style="padding: 30px;">
            <p style="color: #333;">Dear <strong>{student_name}</strong>,</p>
            <p style="color: #555;">Your One-Time Password (OTP) for the SWC Election login is:</p>
            <div style="text-align: center; margin: 24px 0;">
              <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px;
                           color: #1a237e; background: #f0f4ff; padding: 12px 24px;
                           border-radius: 8px; display: inline-block;">{otp}</span>
            </div>
            <p style="color: #e53935; font-size: 13px;">
              ⏱️ This OTP is valid for <strong>5 minutes only</strong>.
              Do NOT share it with anyone.
            </p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">
              If you did not request this OTP, please ignore this email.
              This is an automated message from the SWC Election system.
            </p>
          </div>
          <div style="background: #f5f5f5; padding: 12px; text-align: center;">
            <p style="color: #aaa; font-size: 11px; margin: 0;">
              © SWC Election Platform — Student Welfare Council
            </p>
          </div>
        </div>
        """
        msg.body = f"""
Dear {student_name},

Your OTP for SWC Election login is: {otp}

This OTP is valid for 5 minutes only.
Do not share this with anyone.

— SWC Election Team
        """
        mail.send(msg)
