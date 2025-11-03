import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///simulator.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes

    # SMTP (Mailgun)
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'gofatoorahhyphen111@gmail.com')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'ldpgkzaqsmeakaxv')
    SMTP_FROM = os.getenv('SMTP_FROM', 'gofatoorahhyphen111@gmail.com')

    # Admin
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@asphare.com')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

    # Simulator
    DEFAULT_USER_COUNT = 45
    DEFAULT_HISTORY_DAYS = 180
    WORKING_HOURS_START = 9
    WORKING_HOURS_END = 18
    EVENT_BATCH_SIZE = 50
    MAX_EVENT_BATCH_SIZE = 1000
    RETENTION_DAYS = 180
