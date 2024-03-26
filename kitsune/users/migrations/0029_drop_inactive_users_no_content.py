
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db import migrations

from kitsune.users.utils import anonymize_user

def check_for_user_content(user):
    """Check if a user has any content that is live,
    not archived """
    return ( 
        user.revisions.filter(is_approved=True, is_archived=False).exists() or
        user.questions.filter(is_archived=False).exists() or
        user.questions.filter(solution__creator=user, is_spam=False).exists()
    )

def drop_inactive_users_no_content(apps, schema_editor):
    """Drop inactive users with no content."""
    User = apps.get_model("auth", "User")
    for user in User.objects.filter(
            is_active=False,
            last_login__lte=datetime.now() - timedelta(days=365),
            is_superuser=False,
        ):
        if check_for_user_content(user):
            anonymize_user(user)
        else:
            user.delete()

class Migration(migrations.Migration):
    dependencies = [
        ("users", "0028_alter_profile_bio_and_upper_name_idx"),
    ]

    operations = [
        migrations.RunPython(drop_inactive_users_no_content, 
                             reverse_code=migrations.RunPython.noop),
    ]
