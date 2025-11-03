import random

BEHAVIOR_PATTERNS = {
    'high_performer': {
        'percentage': 0.20,
        'activity_multiplier': 1.75,
        'slack_daily': (40, 50),
        'teams_daily': (20, 25),
        'jira_daily': (10, 15),
        'response_time_minutes': (5, 30),
        'work_pattern': 'consistent',
        'description': 'Consistent high performance, occasional late nights'
    },
    'steady_contributor': {
        'percentage': 0.50,
        'activity_multiplier': 1.0,
        'slack_daily': (20, 30),
        'teams_daily': (10, 15),
        'jira_daily': (5, 8),
        'response_time_minutes': (60, 120),
        'work_pattern': 'regular',
        'description': 'Regular 9-6, predictable activity'
    },
    'at_risk': {
        'percentage': 0.20,
        'activity_multiplier': 0.45,
        'slack_daily': (5, 15),
        'teams_daily': (3, 8),
        'jira_daily': (2, 5),
        'response_time_minutes': (240, 480),
        'work_pattern': 'irregular',
        'description': 'Declining activity, irregular patterns'
    },
    'onboarding': {
        'percentage': 0.10,
        'activity_multiplier': 0.70,
        'slack_daily': (10, 25),
        'teams_daily': (8, 15),
        'jira_daily': (3, 7),
        'response_time_minutes': (60, 180),
        'work_pattern': 'learning',
        'description': 'Ramping up, asking questions'
    }
}

FIRST_NAMES = [
    'Sarah', 'Michael', 'Emma', 'James', 'Olivia', 'William', 'Ava', 'Robert',
    'Isabella', 'David', 'Sophia', 'Joseph', 'Charlotte', 'Thomas', 'Amelia',
    'Christopher', 'Emily', 'Daniel', 'Harper', 'Matthew', 'Evelyn', 'Andrew',
    'Abigail', 'Joshua', 'Elizabeth', 'Ryan', 'Sofia', 'Nicholas', 'Avery', 'Brandon'
]

LAST_NAMES = [
    'Chen', 'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
    'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson',
    'Taylor', 'Thomas', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White',
    'Harris', 'Clark', 'Lewis', 'Robinson', 'Walker', 'Young', 'Hall'
]

ROLES = [
    'Software Engineer', 'Senior Engineer', 'Product Manager', 'Designer',
    'Data Analyst', 'DevOps Engineer', 'QA Engineer', 'Project Manager',
    'Team Lead', 'Engineering Manager', 'UX Researcher', 'Technical Writer'
]


def generate_user_profiles(count=45):
    """Generate realistic user profiles with behavior patterns"""
    profiles = []
    used_names = set()

    # Calculate distribution
    distribution = {}
    for pattern, config in BEHAVIOR_PATTERNS.items():
        distribution[pattern] = int(count * config['percentage'])

    # Adjust for rounding
    total = sum(distribution.values())
    if total < count:
        distribution['steady_contributor'] += (count - total)

    user_id = 1
    for pattern, num_users in distribution.items():
        for _ in range(num_users):
            # Generate unique name
            while True:
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
                name = f"{first} {last}"
                if name not in used_names:
                    used_names.add(name)
                    break

            profile = {
                'id': f'user_{user_id:03d}',
                'name': name,
                'email': f"{first.lower()}.{last.lower()}@asphare.com",
                'role': random.choice(ROLES),
                'behavior_pattern': pattern,
                'activity_multiplier': BEHAVIOR_PATTERNS[pattern]['activity_multiplier']
            }
            profiles.append(profile)
            user_id += 1

    random.shuffle(profiles)
    return profiles