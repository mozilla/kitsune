from datetime import timedelta
import time
import importlib

from django.db import migrations
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model


def delete_inactive_users(apps, schema_editor):
    """
    Delete users who haven't logged in for over three years.
    """
    User = get_user_model()
    
    utils_module = importlib.import_module('kitsune.users.utils')
    delete_user_pipeline = utils_module.delete_user_pipeline
    
    has_content_criteria = (
        Q(answer_votes__isnull=False)
        | Q(answers__isnull=False)
        | Q(award_creator__isnull=False)
        | Q(badge__isnull=False)
        | Q(created_revisions__isnull=False)
        | Q(gallery_images__isnull=False)
        | Q(gallery_videos__isnull=False)
        | Q(outbox__isnull=False)
        | Q(poll_votes__isnull=False)
        | Q(post__isnull=False)
        | Q(question_votes__isnull=False)
        | Q(questions__isnull=False)
        | Q(readied_for_l10n_revisions__isnull=False)
        | Q(reviewed_revisions__isnull=False)
        | Q(thread__isnull=False)
        | Q(wiki_post_set__isnull=False)
        | Q(wiki_thread_set__isnull=False)
        | Q(locales_leader__isnull=False)
        | Q(locales_reviewer__isnull=False)
        | Q(locales_editor__isnull=False)
        | Q(wiki_contributions__isnull=False)
    )
    
    cutoff_date = timezone.now() - timedelta(days=3*365)
    
    query = User.objects.filter(last_login__lt=cutoff_date)
    total_users = query.count()

    if total_users == 0:
        print("No inactive users to delete")
        return

    print(f"Starting deletion of {total_users:,} inactive users")
    start_time = time.time()
    deleted_count = 0
    batch_size = 1000
    pipeline_count = 0
    direct_count = 0
    
    last_id = 0
    while True:
        batch = list(
            query.filter(id__gt=last_id)
            .order_by('id')
            .annotate(has_content=has_content_criteria)
            [:batch_size]
        )
        if not batch:
            break
        last_id = max(user.id for user in batch)
        
        users_with_content = [user for user in batch if user.has_content]
        users_no_content = [user for user in batch if not user.has_content]
        
        for user in users_with_content:
            try:
                delete_user_pipeline(user)
                pipeline_count += 1
            except Exception as e:
                print(f"Error deleting user {user.id}: {e}")
        
        if users_no_content:
            try:
                user_ids = [user.id for user in users_no_content]
                User._base_manager.filter(id__in=user_ids).delete()
                direct_count += len(users_no_content)
            except Exception as e:
                print(f"Error batch deleting users: {e}")
        
        # Update progress reporting
        batch_count = len(batch)
        deleted_count += batch_count
        
        elapsed_time = time.time() - start_time
        progress_pct = (deleted_count/total_users*100) if total_users > 0 else 0
        avg_time = elapsed_time / deleted_count if deleted_count > 0 else 0
        remaining_time = (total_users - deleted_count) * avg_time if deleted_count > 0 else 0
        current_rate = deleted_count / elapsed_time * 60 if elapsed_time > 0 else 0
        
        print(
            f"Progress: {deleted_count:,}/{total_users:,} ({progress_pct:.1f}%) | "
            f"Pipeline: {pipeline_count:,} | Direct: {direct_count:,} | "
            f"Rate: {current_rate:.1f} users/min | "
            f"Remaining: {timedelta(seconds=int(remaining_time))}"
        )
    
    total_time = time.time() - start_time
    print(
        f"Deletion Complete: {deleted_count:,} users deleted "
        f"({pipeline_count:,} pipeline, {direct_count:,} direct) "
        f"in {timedelta(seconds=int(total_time))}"
    )


def reverse_migration(apps, schema_editor):
    """
    No reverse migration possible since deletion cannot be undone
    """
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0034_batch_delete_non_migrated_users"),
    ]

    operations = [
        migrations.RunPython(
            delete_inactive_users,
            reverse_migration,
        ),
    ] 