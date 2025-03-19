from django.db import migrations, transaction
from django.db.models import Q


def delete_non_migrated_users(apps, schema_editor):
    """
    Delete users where is_fxa_migrated is False and who aren't creators of 
    any revision, question, or answer, and who don't have any votes or messages
    """
    User = apps.get_model('auth', 'User')
    
    with transaction.atomic():
        users_to_delete = User.objects.filter(
            profile__is_fxa_migrated=False
        ).exclude(
            Q(created_revisions__isnull=False) |
            Q(questions__isnull=False) |
            Q(answers__isnull=False) |
            Q(question_votes__isnull=False) |
            Q(answer_votes__isnull=False) |
            Q(outbox__isnull=False) |
            Q(inbox__isnull=False) |
            Q(inboxmessage__isnull=False)
        )
        
        users_to_delete.delete()


def reverse_migration(apps, schema_editor):
    """
    No reverse migration possible since deletion cannot be undone
    """
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0032_profile_account_type_alter_profile_user'),
    ]

    operations = [
        migrations.RunPython(
            delete_non_migrated_users,
            reverse_migration,
        ),
    ] 
