"""
Setup script for ASPHARE Event Simulator
Usage:
    python setup.py --init-db              # Initialize database
    python setup.py --set-users 45         # Set user count
    python setup.py --seed-history 180     # Generate 180 days of events
    python setup.py --all                  # Do everything
"""

import sys
import argparse
from datetime import datetime


def init_database():
    """Initialize database schema"""
    from app import app, db

    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Database initialized")


def seed_users(count=45):
    """Seed database with fictional users"""
    from app import app, db, User
    from user_profiles import generate_user_profiles

    with app.app_context():
        # Check if users already exist
        existing = User.query.count()
        if existing > 0:
            print(f"Database already has {existing} users")
            response = input("Delete and recreate? (y/n): ")
            if response.lower() != 'y':
                return
            User.query.delete()
            db.session.commit()

        print(f"Generating {count} user profiles...")
        profiles = generate_user_profiles(count)

        for profile in profiles:
            user = User(**profile)
            db.session.add(user)

        db.session.commit()
        print(f"✓ Created {count} users")

        # Show distribution
        from user_profiles import BEHAVIOR_PATTERNS
        for pattern in BEHAVIOR_PATTERNS.keys():
            count = User.query.filter_by(behavior_pattern=pattern).count()
            print(f"  - {pattern}: {count} users")


def seed_historical_events(days=180):
    """Generate historical events"""
    from app import app, db, User, Event, ConfigSetting, ReplayProgress
    from event_generator import EventGenerator

    with app.app_context():
        users = User.query.all()
        if not users:
            print("Error: No users in database. Run --set-users first")
            return

        # Check if historical events exist
        existing = Event.query.filter_by(source='historical').count()
        if existing > 0:
            print(f"Database already has {existing} historical events")
            response = input("Delete and regenerate? (y/n): ")
            if response.lower() != 'y':
                return
            Event.query.filter_by(source='historical').delete()
            db.session.commit()

        print(f"\n Generating {days} days of historical events...")
        print(f"   Users: {len(users)}")
        print(f"   Estimated events: ~{len(users) * days * 30}")
        print(f"   This may take 15-30 minutes...\n")

        start_time = datetime.now()

        events = EventGenerator.generate_historical_events(users, days=days)

        # Batch insert for performance
        print("\nSaving events to database...")
        batch_size = 1000
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            for event_data in batch:
                event = Event(**event_data)
                db.session.add(event)
            db.session.commit()
            print(f"  Saved {min(i + batch_size, len(events))}/{len(events)} events")

        # Initialize replay progress
        replay = ReplayProgress.query.first()
        if not replay:
            replay = ReplayProgress()
            db.session.add(replay)

        replay.total_events = len(events)
        replay.consumed_events = 0
        replay.in_progress = False

        # Set mode to setup
        mode_setting = ConfigSetting.query.get('mode')
        if mode_setting:
            mode_setting.value = 'setup'
        else:
            db.session.add(ConfigSetting(key='mode', value='setup'))

        db.session.commit()

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n✓ Generated {len(events)} historical events in {elapsed:.1f}s")
        print(f"  Ready for replay mode")


def set_user_count(count):
    """Update user count in config"""
    from app import app, db, ConfigSetting
    import json

    with app.app_context():
        setting = ConfigSetting.query.get('user_count')
        if setting:
            setting.value = str(count)
        else:
            setting = ConfigSetting(key='user_count', value=str(count))
            db.session.add(setting)

        db.session.commit()
        print(f"✓ User count set to {count}")


def show_status():
    """Show current database status"""
    from app import app, db, User, Event, ConfigSetting

    with app.app_context():
        users = User.query.count()
        total_events = Event.query.count()
        historical = Event.query.filter_by(source='historical').count()
        daily = Event.query.filter_by(source='daily').count()
        manual = Event.query.filter_by(source='manual').count()
        consumed = Event.query.filter_by(consumed=True).count()

        print("\n" + "=" * 50)
        print("ASPHARE Simulator Status")
        print("=" * 50)
        print(f"Users:              {users}")
        print(f"Total Events:       {total_events:,}")
        print(f"  - Historical:     {historical:,}")
        print(f"  - Daily:          {daily:,}")
        print(f"  - Manual:         {manual:,}")
        print(f"Consumed Events:    {consumed:,}")
        print(f"Unconsumed:         {total_events - consumed:,}")

        mode_setting = ConfigSetting.query.get('mode')
        mode = mode_setting.value if mode_setting else 'unknown'
        print(f"Current Mode:       {mode}")
        print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description='ASPHARE Event Simulator Setup')
    parser.add_argument('--init-db', action='store_true', help='Initialize database')
    parser.add_argument('--set-users', type=int, metavar='N', help='Create N users (30-60)')
    parser.add_argument('--seed-history', type=int, metavar='DAYS', help='Generate historical events')
    parser.add_argument('--status', action='store_true', help='Show current status')
    parser.add_argument('--all', action='store_true', help='Initialize everything')

    args = parser.parse_args()

    if args.all:
        init_database()
        seed_users(45)
        seed_historical_events(180)
        show_status()
    elif args.init_db:
        init_database()
    elif args.set_users:
        if 30 <= args.set_users <= 60:
            init_database()
            seed_users(args.set_users)
            set_user_count(args.set_users)
        else:
            print("Error: User count must be between 30 and 60")
    elif args.seed_history:
        if args.seed_history in [14, 30, 90, 180]:
            seed_historical_events(args.seed_history)
        else:
            print("Error: History days must be 14, 30, 90, or 180")
    elif args.status:
        show_status()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
