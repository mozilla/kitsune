from kitsune.users.tests import GroupFactory, UserFactory

GROUPS = {
    "staff": 15,
    "small_group": 10,
    "medium_group": 15,
    "large_group": 1000,
    "xlarge_group": 5000,
}


def generate_sampledata(options):
    """Generate user and group sample data."""
    for group_name, user_count in GROUPS.items():
        g = GroupFactory(name=group_name)
        g.save()
        print(f"Created group {group_name}")

        # Make the users for this group
        for _ in range(user_count):
            user_name = f"{group_name}User{_}"
            u = UserFactory(username=user_name, groups=[g])
            u.save()
            print(f"Created user {user_name}")