from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)
    behavior_pattern = db.Column(db.String(50), nullable=False)
    activity_multiplier = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'behavior_pattern': self.behavior_pattern,
            'activity_multiplier': self.activity_multiplier
        }


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.String(50), primary_key=True, default=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(20), nullable=False)  # slack, teams, jira
    event_type = db.Column(db.String(50), nullable=False)
    event_category = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    payload = db.Column(db.Text, nullable=False)  # JSON string
    consumed = db.Column(db.Boolean, default=False, index=True)
    source = db.Column(db.String(20), default='daily')  # historical, daily, manual
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='events')

    def to_dict(self):
        return {
            'event_id': self.id,
            'user_id': self.user_id,
            'platform': self.platform,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'timestamp': self.timestamp.isoformat() + 'Z',
            'payload': json.loads(self.payload),
            'consumed': self.consumed,
            'source': self.source
        }


class EventCategory(db.Model):
    __tablename__ = 'event_categories'

    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(50), nullable=False)
    platform = db.Column(db.String(20), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('platform', 'event_type', name='unique_platform_event'),
    )


class AuthToken(db.Model):
    __tablename__ = 'auth_tokens'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ScheduledEvent(db.Model):
    __tablename__ = 'scheduled_events'

    id = db.Column(db.Integer, primary_key=True)
    schedule_time = db.Column(db.DateTime, nullable=False)
    platform = db.Column(db.String(20), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'))
    params = db.Column(db.Text)  # JSON string
    executed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ReplayProgress(db.Model):
    __tablename__ = 'replay_progress'

    id = db.Column(db.Integer, primary_key=True)
    total_events = db.Column(db.Integer, default=0)
    consumed_events = db.Column(db.Integer, default=0)
    in_progress = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConfigSetting(db.Model):
    __tablename__ = 'config'

    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)