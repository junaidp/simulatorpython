from datetime import datetime, timedelta
import random
import json

from user_profiles import BEHAVIOR_PATTERNS


class EventGenerator:

    SLACK_EVENTS = {
        'message.channel': {'category': 'communication', 'weight': 35},
        'message.direct': {'category': 'communication', 'weight': 20},
        'message.thread': {'category': 'communication', 'weight': 15},
        'reaction.add': {'category': 'communication', 'weight': 20},
        'mention': {'category': 'communication', 'weight': 5},
        'file.upload': {'category': 'collaboration', 'weight': 3},
        'channel.join': {'category': 'collaboration', 'weight': 1},
        'status.update': {'category': 'communication', 'weight': 1}
    }

    TEAMS_EVENTS = {
        'message.channel': {'category': 'communication', 'weight': 35},
        'message.chat': {'category': 'communication', 'weight': 25},
        'meeting.scheduled': {'category': 'collaboration', 'weight': 10},
        'meeting.joined': {'category': 'collaboration', 'weight': 10},
        'meeting.ended': {'category': 'collaboration', 'weight': 10},
        'file.shared': {'category': 'collaboration', 'weight': 5},
        'reaction.add': {'category': 'communication', 'weight': 4},
        'mention': {'category': 'communication', 'weight': 1}
    }

    JIRA_EVENTS = {
        'issue.updated': {'category': 'task_management', 'weight': 35},
        'issue.status_changed': {'category': 'task_management', 'weight': 25},
        'issue.commented': {'category': 'task_management', 'weight': 20},
        'issue.created': {'category': 'task_management', 'weight': 10},
        'issue.assigned': {'category': 'task_management', 'weight': 5},
        'issue.priority_changed': {'category': 'task_management', 'weight': 3},
        'attachment.added': {'category': 'task_management', 'weight': 2}
    }

    CHANNELS = ['#engineering', '#general', '#product', '#design', '#random', '#support']
    PROJECTS = ['PROJ-A', 'PROJ-B', 'PROJ-C', 'TEAM-X', 'INFRA-Y']
    ISSUE_TYPES = ['Bug', 'Task', 'Story', 'Epic', 'Subtask']
    PRIORITIES = ['Highest', 'High', 'Medium', 'Low', 'Lowest']
    STATUSES = ['To Do', 'In Progress', 'In Review', 'Done']

    @staticmethod
    def weighted_choice(events_dict):
        """Select event type based on weights"""
        events = list(events_dict.keys())
        weights = [events_dict[e]['weight'] for e in events]
        return random.choices(events, weights=weights)[0]

    @staticmethod
    def generate_slack_event(user, event_type, timestamp):
        """Generate Slack event payload"""
        base = {
            'user_name': user.name,
            'user_id': user.id
        }

        if 'message' in event_type:
            messages = [
                "Sprint planning meeting starts in 10 minutes",
                "Updated the documentation for the new API",
                "Can someone review my PR?",
                "Great work on the last release!",
                "Has anyone encountered this error before?",
                "Meeting notes are in the shared drive",
                "Thanks for the quick turnaround on this",
                "I'll take a look at this after lunch"
            ]
            base.update({
                'channel_id': f'C{random.randint(10000, 99999)}',
                'channel_name': random.choice(EventGenerator.CHANNELS),
                'message_text': random.choice(messages),
                'has_mentions': random.random() < 0.2,
                'thread_ts': f'{timestamp.timestamp()}' if 'thread' in event_type else None
            })

        elif event_type == 'reaction.add':
            base.update({
                'channel_id': f'C{random.randint(10000, 99999)}',
                'reaction': random.choice(['thumbsup', 'eyes', 'tada', 'rocket', 'heart']),
                'message_ts': f'{(timestamp - timedelta(minutes=random.randint(1, 60))).timestamp()}'
            })

        elif event_type == 'file.upload':
            base.update({
                'channel_id': f'C{random.randint(10000, 99999)}',
                'file_name': random.choice(['design_mockup.png', 'report.pdf', 'data_analysis.xlsx']),
                'file_type': random.choice(['image', 'pdf', 'document'])
            })

        elif event_type == 'mention':
            base.update({
                'channel_id': f'C{random.randint(10000, 99999)}',
                'mentioned_user_id': f'user_{random.randint(1, 60):03d}',
                'message_text': "Can you take a look at this when you get a chance?"
            })

        return base

    @staticmethod
    def generate_teams_event(user, event_type, timestamp):
        """Generate Teams event payload"""
        base = {
            'user_name': user.name,
            'user_id': user.id
        }

        if 'message' in event_type:
            base.update({
                'channel_id': f'T{random.randint(10000, 99999)}',
                'message_text': random.choice([
                    "Let's sync up this afternoon",
                    "Sharing the latest metrics",
                    "Who's available for a quick call?",
                    "Updated the project timeline"
                ])
            })

        elif 'meeting' in event_type:
            base.update({
                'meeting_id': f'M{random.randint(10000, 99999)}',
                'meeting_title': random.choice([
                    'Daily Standup', 'Sprint Planning', 'Team Sync',
                    '1:1 Meeting', 'Design Review', 'Retrospective'
                ]),
                'duration_minutes': random.choice([15, 30, 60]),
                'participants': random.randint(2, 8)
            })

        elif event_type == 'file.shared':
            base.update({
                'file_name': random.choice(['presentation.pptx', 'requirements.docx', 'budget.xlsx']),
                'file_size_kb': random.randint(100, 5000)
            })

        return base

    @staticmethod
    def generate_jira_event(user, event_type, timestamp):
        """Generate Jira event payload"""
        base = {
            'user_name': user.name,
            'user_id': user.id,
            'issue_key': f'{random.choice(EventGenerator.PROJECTS)}-{random.randint(100, 999)}',
            'project_id': random.choice(EventGenerator.PROJECTS)
        }

        if event_type == 'issue.created':
            base.update({
                'issue_type': random.choice(EventGenerator.ISSUE_TYPES),
                'priority': random.choice(EventGenerator.PRIORITIES),
                'summary': random.choice([
                    'Implement user authentication',
                    'Fix login page bug',
                    'Update API documentation',
                    'Optimize database queries'
                ])
            })

        elif event_type == 'issue.status_changed':
            base.update({
                'from_status': random.choice(EventGenerator.STATUSES[:-1]),
                'to_status': random.choice(EventGenerator.STATUSES[1:])
            })

        elif event_type == 'issue.commented':
            base.update({
                'comment': random.choice([
                    'Working on this now',
                    'Needs more clarification',
                    'Ready for review',
                    'Blocked by dependency'
                ])
            })

        elif event_type == 'issue.assigned':
            base.update({
                'assigned_to': f'user_{random.randint(1, 60):03d}'
            })

        elif event_type == 'issue.priority_changed':
            base.update({
                'from_priority': random.choice(EventGenerator.PRIORITIES),
                'to_priority': random.choice(EventGenerator.PRIORITIES)
            })

        return base

    @staticmethod
    def generate_event(user, platform, timestamp, source='daily'):
        """Generate a single event for a user"""
        if platform == 'slack':
            event_type = EventGenerator.weighted_choice(EventGenerator.SLACK_EVENTS)
            payload = EventGenerator.generate_slack_event(user, event_type, timestamp)
            category = EventGenerator.SLACK_EVENTS[event_type]['category']

        elif platform == 'teams':
            event_type = EventGenerator.weighted_choice(EventGenerator.TEAMS_EVENTS)
            payload = EventGenerator.generate_teams_event(user, event_type, timestamp)
            category = EventGenerator.TEAMS_EVENTS[event_type]['category']

        elif platform == 'jira':
            event_type = EventGenerator.weighted_choice(EventGenerator.JIRA_EVENTS)
            payload = EventGenerator.generate_jira_event(user, event_type, timestamp)
            category = EventGenerator.JIRA_EVENTS[event_type]['category']

        else:
            raise ValueError(f"Unknown platform: {platform}")

        return {
            'user_id': user.id,
            'platform': platform,
            'event_type': event_type,
            'event_category': category,
            'timestamp': timestamp,
            'payload': json.dumps(payload),
            'consumed': False,
            'source': source
        }

    @staticmethod
    def calculate_daily_events(user, platform):
        """Calculate number of events per day for user on platform"""
        pattern = BEHAVIOR_PATTERNS[user.behavior_pattern]

        if platform == 'slack':
            base_range = pattern['slack_daily']
        elif platform == 'teams':
            base_range = pattern['teams_daily']
        elif platform == 'jira':
            base_range = pattern['jira_daily']
        else:
            base_range = (5, 10)

        return random.randint(base_range[0], base_range[1])

    @staticmethod
    def is_working_hours(dt, start_hour=9, end_hour=18):
        """Check if datetime is within working hours"""
        return (dt.weekday() < 5 and  # Monday-Friday
                start_hour <= dt.hour < end_hour)

    @staticmethod
    def generate_historical_events(users, days=180, platforms=['slack', 'teams', 'jira']):
        """Generate historical events for all users"""
        events = []
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

    #
        print(f" DEBUG INFO:")
        print(f"   Start date: {start_date.strftime('%Y-%m-%d')}")
        print(f"   End date: {end_date.strftime('%Y-%m-%d')}")
        print(f"   Total days: {(end_date - start_date).days}")
        print(f"   Start weekday: {start_date.weekday()} (0=Mon, 6=Sun)")
        print()

        print(f"Generating {days} days of historical events for {len(users)} users...")

        current_date = start_date
        days_processed = 0  #

        while current_date < end_date:
                days_processed += 1

                if current_date.weekday() < 5:  # Weekdays only
                    print(f"  Processing day {days_processed}: {current_date.strftime('%Y-%m-%d')}")

                for user in users:
                    for platform in platforms:
                        daily_events = EventGenerator.calculate_daily_events(user, platform)

                        for _ in range(daily_events):
                            hour = random.randint(9, 17)
                            minute = random.randint(0, 59)
                            event_time = current_date.replace(
                                hour=hour,
                                minute=minute,
                                second=random.randint(0, 59)
                            )

                            event = EventGenerator.generate_event(
                                user, platform, event_time, source='historical'
                            )
                            events.append(event)

                current_date += timedelta(days=1)

        if current_date.day == 1:
            print(f"  Generated through {current_date.strftime('%Y-%m')}")

        print(f"\n Total days processed: {days_processed}")
        print(f"Generated {len(events)} total historical events")
        return events