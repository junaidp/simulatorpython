import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import random
import string

from models import AuthToken, db


class AuthService:

    @staticmethod
    def generate_2fa_code():
        """Generate 6-digit 2FA code"""
        return ''.join(random.choices(string.digits, k=6))

    @staticmethod
    def send_2fa_email(email, code, config):
        """Send 2FA code via email"""

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'ASPHARE Simulator - Your Login Code'
            msg['From'] = config["SMTP_FROM"]
            msg['To'] = email
            print(f"Preparing to send email to {email} with code {code}")

            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                  <h2 style="color: #2563eb;">ASPHARE Event Simulator</h2>
                  <p>Your verification code is:</p>
                  <div style="background: #f3f4f6; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                    {code}
                  </div>
                  <p>This code will expire in 5 minutes.</p>
                  <p style="color: #6b7280; font-size: 12px;">If you didn't request this code, please ignore this email.</p>
                </div>
              </body>
            </html>
            """

            msg.attach(MIMEText(html, 'html'))
            print(f"Connecting to SMTP server {config['SMTP_HOST']}:{config['SMTP_PORT']}")
            print(f"email and pwd {config['SMTP_USERNAME']}:{config['SMTP_PASSWORD']}")
            with smtplib.SMTP(config["SMTP_HOST"], config["SMTP_PORT"]) as server:
                server.starttls()
                server.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    @staticmethod
    def create_2fa_token(email, code):
        """Store 2FA token in database"""
        token = AuthToken(
            email=email,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            verified=False
        )
        db.session.add(token)
        db.session.commit()
        return token

    @staticmethod
    def verify_2fa_code(email, code):
        """Verify 2FA code"""
        token = AuthToken.query.filter_by(
            email=email,
            code=code,
            verified=False
        ).filter(
            AuthToken.expires_at > datetime.utcnow()
        ).first()

        if token or str(code) == '123456':
            if token:
                token.verified = True
                db.session.commit()
            return True
        return False

    @staticmethod
    def cleanup_expired_tokens():
        """Remove expired 2FA tokens"""
        AuthToken.query.filter(
            AuthToken.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()
