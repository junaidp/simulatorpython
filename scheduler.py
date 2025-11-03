from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import time
import random

def generate_daily_events():
    """Generate events for current day"""
    from app import app, db, User, Event, ConfigSetting
    from event_generator import EventGenerator

    with app.app_context():
        # Check if we're in daily mode
        mode_setting = ConfigSetting.query.get('mode')
        if not mode_setting or mode_setting.value != 'daily':
            print("Not in daily mode, skipping generation")
            return

        # Check if within working hours
        now = datetime.utcnow()
        if not EventGenerator.is_working_hours(now):
            print(f"Outside working hours: {now.hour}:00")
            return

        # Get active platforms
        platforms_setting = ConfigSetting.query.get('platforms')
        if platforms_setting:
            platforms = json.loads(platforms_setting.value)
        else:
            platforms = ['slack', 'teams', 'jira']

        # Get all users
        users = User.query.all()
        if not users:
            print("No users found")
            return

        # Generate events for random subset of users (simulate realistic activity)
        active_users = random.sample(users, k=min(len(users), random.randint(10, 30)))

        events_generated = 0
        for user in active_users:
            for platform in platforms:
                # 30% chance to generate event for this user/platform combo
                if random.random() < 0.3:
                    timestamp = now + timedelta(seconds=random.randint(0, 300))
                    event_data = EventGenerator.generate_event(user, platform, timestamp, source='daily')

                    event = Event(**event_data)
                    db.session.add(event)
                    events_generated += 1

        db.session.commit()
        print(f"Generated {events_generated} daily events at {now.strftime('%Y-%m-%d %H:%M:%S')}")

def check_scheduled_events():
    """Check and execute scheduled events"""
    from app import app, db, ScheduledEvent, User, Event
    from event_generator import EventGenerator

    with app.app_context():
        now = datetime.utcnow()

        # Get due scheduled events
        due_events = ScheduledEvent.query.filter(
            ScheduledEvent.schedule_time <= now,
            ScheduledEvent.executed == False
        ).all()

        for scheduled in due_events:
            user = User.query.get(scheduled.user_id) if scheduled.user_id else random.choice(User.query.all())

            if user:
                event_data = EventGenerator.generate_event(
                    user,
                    scheduled.platform,
                    now,
                    source='manual'
                )

                event = Event(**event_data)
                db.session.add(event)

                scheduled.executed = True

        db.session.commit()

        if due_events:
            print(f"Executed {len(due_events)} scheduled events")

def main():
    """Main scheduler loop"""
    print("Starting ASPHARE Event Generator Scheduler...")

    scheduler = BackgroundScheduler()

    # Generate events every 5 minutes during working hours
    scheduler.add_job(
        generate_daily_events,
        CronTrigger(minute='*/5', hour='9-17', day_of_week='mon-fri'),
        id='daily_events',
        name='Generate daily events'
    )

    # Check scheduled events every minute
    scheduler.add_job(
        check_scheduled_events,
        CronTrigger(minute='*'),
        id='scheduled_events',
        name='Check scheduled events'
    )

    scheduler.start()
    print("Scheduler started successfully")
    print("Jobs:")
    for job in scheduler.get_jobs():
        print(f"  - {job.name} (ID: {job.id})")

    try:
        # Keep the script running
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        print("\nShutting down scheduler...")
        scheduler.shutdown()
        print("Scheduler stopped")

if __name__ == '__main__':
    main()
