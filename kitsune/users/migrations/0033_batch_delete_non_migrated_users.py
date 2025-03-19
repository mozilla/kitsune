from django.db import migrations
from django.db.models import Q


def delete_non_migrated_users(apps, schema_editor):
    """
    Delete users where is_fxa_migrated is False and who aren't creators/owners/users of
    any content or relationships in the system
    """
    User = apps.get_model('auth', 'User')
    
    users_to_delete = User.objects.filter(
        profile__is_fxa_migrated=False
    ).exclude(
        Q(answer_votes__isnull=False) |
        Q(answers__isnull=False) |
        Q(award_creator__isnull=False) |
        Q(badge__isnull=False) |
        Q(created_revisions__isnull=False) |
        Q(gallery_images__isnull=False) |
        Q(gallery_videos__isnull=False) |
        Q(inboxmessage__isnull=False) |
        Q(outbox__isnull=False) |
        Q(poll_votes__isnull=False) |
        Q(post__isnull=False) |
        Q(question_votes__isnull=False) |
        Q(questions__isnull=False) |
        Q(readied_for_l10n_revisions__isnull=False) |
        Q(reviewed_revisions__isnull=False) |
        Q(thread__isnull=False) |
        Q(wiki_post_set__isnull=False) |
        Q(wiki_thread_set__isnull=False)
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
