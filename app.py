import random

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
from datetime import datetime, timedelta
import json

from auth import AuthService
from config import Config
from models import Event, ConfigSetting, User, ReplayProgress, db, ScheduledEvent
from user_generator import EventGenerator

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
CORS(app)


# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_authenticated' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# UI ROUTES
# ============================================================================

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Simple authentication (in production, use proper password hashing)
        if email == app.config['ADMIN_EMAIL'] and password == app.config['ADMIN_PASSWORD']:
            # Generate and send 2FA code
            code = AuthService.generate_2fa_code()
            AuthService.create_2fa_token(email, code)

            # In development, just return the code (remove in production)
            if app.debug:
                return jsonify({'success': True, 'dev_code': code})

            # Send email
            if AuthService.send_2fa_email(email, code, app.config):
                return jsonify({'success': True, 'message': '2FA code sent to email'})
            else:
                return jsonify({'success': False, 'message': 'Failed to send 2FA code'}), 500
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    return render_template('login.html')


@app.route('/verify-2fa', methods=['POST'])
def verify_2fa():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')

    if AuthService.verify_2fa_code(email, code):
        session['user_authenticated'] = True
        session['user_email'] = email
        session.permanent = True
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid or expired code'}), 401


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/ui/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/ui/config')
@login_required
def config_page():
    return render_template('config.html')


@app.route('/ui/manual')
@login_required
def manual_events():
    return render_template('manual.html')


@app.route('/ui/api-docs')
@login_required
def api_docs():
    return render_template('api_docs.html')


# ============================================================================
# API ENDPOINTS - Event Polling (Called by n8n)
# ============================================================================

@app.route('/api/slack/events', methods=['GET'])
def get_slack_events():
    """Fetch unconsumed Slack events"""
    limit = request.args.get('limit', app.config['EVENT_BATCH_SIZE'], type=int)
    limit = min(limit, app.config['MAX_EVENT_BATCH_SIZE'])

    events = Event.query.filter_by(
        platform='slack',
        consumed=False
    ).order_by(Event.timestamp.asc()).limit(limit).all()

    # Mark as consumed
    for event in events:
        event.consumed = True
    db.session.commit()

    return jsonify([event.to_dict() for event in events])


@app.route('/api/teams/events', methods=['GET'])
def get_teams_events():
    """Fetch unconsumed Teams events"""
    limit = request.args.get('limit', app.config['EVENT_BATCH_SIZE'], type=int)
    limit = min(limit, app.config['MAX_EVENT_BATCH_SIZE'])

    events = Event.query.filter_by(
        platform='teams',
        consumed=False
    ).order_by(Event.timestamp.asc()).limit(limit).all()

    # Mark as consumed
    for event in events:
        event.consumed = True
    db.session.commit()

    return jsonify([event.to_dict() for event in events])


@app.route('/api/jira/events', methods=['GET'])
def get_jira_events():
    """Fetch unconsumed Jira events"""
    limit = request.args.get('limit', app.config['EVENT_BATCH_SIZE'], type=int)
    limit = min(limit, app.config['MAX_EVENT_BATCH_SIZE'])

    events = Event.query.filter_by(
        platform='jira',
        consumed=False
    ).order_by(Event.timestamp.asc()).limit(limit).all()

    # Mark as consumed
    for event in events:
        event.consumed = True
    db.session.commit()

    return jsonify([event.to_dict() for event in events])


# ============================================================================
# API ENDPOINTS - Configuration & Control
# ============================================================================

@app.route('/api/config', methods=['GET', 'POST'])
@login_required
def config_api():
    """Get or update simulator configuration"""
    if request.method == 'GET':
        config_data = {}
        settings = ConfigSetting.query.all()
        for setting in settings:
            try:
                config_data[setting.key] = json.loads(setting.value)
            except:
                config_data[setting.key] = setting.value

        # Add default values if not set
        if 'user_count' not in config_data:
            config_data['user_count'] = app.config['DEFAULT_USER_COUNT']
        if 'mode' not in config_data:
            config_data['mode'] = 'daily'
        if 'platforms' not in config_data:
            config_data['platforms'] = ['slack', 'teams', 'jira']

        return jsonify(config_data)

    else:  # POST
        data = request.get_json()

        for key, value in data.items():
            setting = ConfigSetting.query.get(key)
            if setting:
                setting.value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                setting.updated_at = datetime.utcnow()
            else:
                setting = ConfigSetting(
                    key=key,
                    value=json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                )
                db.session.add(setting)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Configuration updated'})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""

    # Total events by platform
    slack_total = Event.query.filter_by(platform='slack').count()
    teams_total = Event.query.filter_by(platform='teams').count()
    jira_total = Event.query.filter_by(platform='jira').count()

    # Today's events
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    slack_today = Event.query.filter(
        Event.platform == 'slack',
        Event.timestamp >= today_start
    ).count()
    teams_today = Event.query.filter(
        Event.platform == 'teams',
        Event.timestamp >= today_start
    ).count()
    jira_today = Event.query.filter(
        Event.platform == 'jira',
        Event.timestamp >= today_start
    ).count()

    # Total and consumed events
    total_events = Event.query.count()
    consumed_events = Event.query.filter_by(consumed=True).count()

    # User count
    user_count = User.query.count()

    # Get mode from config
    mode_setting = ConfigSetting.query.get('mode')
    mode = mode_setting.value if mode_setting else 'daily'

    # Replay progress
    replay = ReplayProgress.query.first()
    replay_progress = 100
    if replay and replay.in_progress and replay.total_events > 0:
        replay_progress = int((replay.consumed_events / replay.total_events) * 100)

    return jsonify({
        'user_count': user_count,
        'total_events': total_events,
        'consumed_events': consumed_events,
        'today_events': slack_today + teams_today + jira_today,
        'mode': mode,
        'replay_progress': replay_progress,
        'is_running': True,  # Check from scheduler status if implemented
        'platforms': {
            'slack': {
                'total': slack_total,
                'today': slack_today
            },
            'teams': {
                'total': teams_total,
                'today': teams_today
            },
            'jira': {
                'total': jira_total,
                'today': jira_today
            }
        }
    })


@app.route('/api/replay/status', methods=['GET'])
def replay_status():
    """Get replay progress status"""
    replay = ReplayProgress.query.first()

    if not replay:
        return jsonify({
            'in_progress': False,
            'total_events': 0,
            'consumed_events': 0,
            'progress_percent': 0
        })

    progress = 0
    if replay.total_events > 0:
        progress = int((replay.consumed_events / replay.total_events) * 100)

    return jsonify({
        'in_progress': replay.in_progress,
        'total_events': replay.total_events,
        'consumed_events': replay.consumed_events,
        'progress_percent': progress,
        'started_at': replay.started_at.isoformat() if replay.started_at else None,
        'completed_at': replay.completed_at.isoformat() if replay.completed_at else None
    })


@app.route('/api/replay/progress', methods=['POST'])
def update_replay_progress():
    """Update replay progress (called by n8n)"""
    data = request.get_json()
    events_processed = data.get('events_processed', 0)

    replay = ReplayProgress.query.first()
    if replay:
        replay.consumed_events += events_processed
        replay.updated_at = datetime.utcnow()

        # Check if replay is complete
        if replay.consumed_events >= replay.total_events:
            replay.in_progress = False
            replay.completed_at = datetime.utcnow()

            # Update mode to daily
            mode_setting = ConfigSetting.query.get('mode')
            if mode_setting:
                mode_setting.value = 'daily'
            else:
                db.session.add(ConfigSetting(key='mode', value='daily'))

        db.session.commit()
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'No replay in progress'}), 404


@app.route('/api/replay/start', methods=['POST'])
@login_required
def start_replay():
    """Manually start historical replay"""
    # Count historical events
    historical_events = Event.query.filter_by(source='historical', consumed=False).count()

    if historical_events == 0:
        return jsonify({'success': False, 'message': 'No historical events to replay'}), 400

    # Create or update replay progress
    replay = ReplayProgress.query.first()
    if not replay:
        replay = ReplayProgress()
        db.session.add(replay)

    replay.total_events = historical_events
    replay.consumed_events = 0
    replay.in_progress = True
    replay.started_at = datetime.utcnow()
    replay.completed_at = None

    # Update mode to replay
    mode_setting = ConfigSetting.query.get('mode')
    if mode_setting:
        mode_setting.value = 'replay'
    else:
        db.session.add(ConfigSetting(key='mode', value='replay'))

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Replay started with {historical_events} events'
    })


# ============================================================================
# API ENDPOINTS - Manual Event Generation
# ============================================================================

@app.route('/api/simulate', methods=['POST'])
@login_required
def simulate_events():
    """Manually generate specific events"""
    data = request.get_json()

    platform = data.get('platform', 'slack')
    event_type = data.get('event_type')
    user_id = data.get('user_id')
    count = data.get('count', 1)

    if not platform or not event_type:
        return jsonify({'success': False, 'message': 'Missing required parameters'}), 400

    # Get user
    if user_id:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        users = [user]
    else:
        users = User.query.all()
        if not users:
            return jsonify({'success': False, 'message': 'No users in database'}), 404
        users = [random.choice(users) for _ in range(count)]

    # Generate events
    generated = []
    for user in users[:count]:
        timestamp = datetime.utcnow()
        event_data = EventGenerator.generate_event(user, platform, timestamp, source='manual')

        event = Event(**event_data)
        db.session.add(event)
        generated.append(event_data)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Generated {len(generated)} events',
        'count': len(generated)
    })


@app.route('/api/schedule', methods=['POST'])
@login_required
def schedule_events():
    """Schedule events for future generation"""
    data = request.get_json()

    schedule_time = data.get('schedule_time')
    platform = data.get('platform')
    event_type = data.get('event_type')
    user_id = data.get('user_id')
    params = data.get('params', {})

    if not schedule_time or not platform or not event_type:
        return jsonify({'success': False, 'message': 'Missing required parameters'}), 400

    try:
        schedule_dt = datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))
    except:
        return jsonify({'success': False, 'message': 'Invalid datetime format'}), 400

    scheduled = ScheduledEvent(
        schedule_time=schedule_dt,
        platform=platform,
        event_type=event_type,
        user_id=user_id,
        params=json.dumps(params)
    )

    db.session.add(scheduled)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Event scheduled successfully',
        'scheduled_id': scheduled.id
    })


@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    """Get all users"""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])


# ============================================================================
# Database Cleanup & Maintenance
# ============================================================================

@app.route('/api/cleanup', methods=['POST'])
@login_required
def cleanup_database():
    """Clean up old events based on retention policy"""
    retention_days = app.config['RETENTION_DAYS']
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

    # Delete old consumed events
    deleted = Event.query.filter(
        Event.consumed == True,
        Event.timestamp < cutoff_date
    ).delete()

    # Cleanup expired auth tokens
    AuthService.cleanup_expired_tokens()

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Deleted {deleted} old events'
    })


# ============================================================================
# Health Check
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
