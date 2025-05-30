from datetime import timedelta
import time

from django.db import migrations
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from kitsune.users.utils import delete_user_pipeline


def delete_inactive_users(apps, schema_editor):
    """
    Delete users who haven't logged in for over three years.
    """
    User = get_user_model()
    
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
    
    # Get users with content (need pipeline deletion)
    users_with_content = User.objects.filter(
        last_login__lt=cutoff_date
    ).filter(has_content_criteria)

    # Get users without content (can be bulk deleted)
    users_without_content = User.objects.filter(
        last_login__lt=cutoff_date
    ).exclude(has_content_criteria)
    
    total_users = users_with_content.count() + users_without_content.count()

    if total_users == 0:
        print("No inactive users to delete")
        return

    print(f"Starting deletion of {total_users:,} inactive users")
    print(f"Users with content: {users_with_content.count():,}")
    print(f"Users without content: {users_without_content.count():,}")
    start_time = time.time()
    processed_count = 0
    pipeline_count = 0
    direct_count = 0
    
    # Process users with content using pipeline
    print("Processing users with content...")
    for user in users_with_content.iterator(chunk_size=1000):
        try:
            delete_user_pipeline(user)
            pipeline_count += 1
        except Exception as e:
            print(f"Error deleting user {user.id}: {e}")
        
        processed_count += 1
        
        # Progress reporting every 1000 users
        if processed_count % 1000 == 0:
            elapsed_time = time.time() - start_time
            progress_pct = (processed_count/total_users*100) if total_users > 0 else 0
            avg_time = elapsed_time / processed_count if processed_count > 0 else 0
            remaining_time = (total_users - processed_count) * avg_time if processed_count > 0 else 0
            current_rate = processed_count / elapsed_time * 60 if elapsed_time > 0 else 0
            
            print(
                f"Progress: {processed_count:,}/{total_users:,} ({progress_pct:.1f}%) | "
                f"Pipeline: {pipeline_count:,} | Direct: {direct_count:,} | "
                f"Rate: {current_rate:.1f} users/min | "
                f"Remaining: {timedelta(seconds=int(remaining_time))}"
            )
    
    # Batch delete users without content
    print("Processing users without content...")
    batch_size = 1000
    users_no_content_batch = []
    
    def bulk_delete_no_content_users():
        nonlocal direct_count
        if users_no_content_batch:
            try:
                User._base_manager.filter(id__in=users_no_content_batch).delete()
                direct_count += len(users_no_content_batch)
                users_no_content_batch.clear()
            except Exception as e:
                print(f"Error batch deleting users: {e}")
    
    for user in users_without_content.iterator(chunk_size=1000):
        users_no_content_batch.append(user.id)
        
        # Bulk delete when batch is full
        if len(users_no_content_batch) >= batch_size:
            bulk_delete_no_content_users()
        
        processed_count += 1
        
        # Progress reporting every 1000 users
        if processed_count % 1000 == 0:
            elapsed_time = time.time() - start_time
            progress_pct = (processed_count/total_users*100) if total_users > 0 else 0
            avg_time = elapsed_time / processed_count if processed_count > 0 else 0
            remaining_time = (total_users - processed_count) * avg_time if processed_count > 0 else 0
            current_rate = processed_count / elapsed_time * 60 if elapsed_time > 0 else 0
            
            print(
                f"Progress: {processed_count:,}/{total_users:,} ({progress_pct:.1f}%) | "
                f"Pipeline: {pipeline_count:,} | Direct: {direct_count:,} | "
                f"Rate: {current_rate:.1f} users/min | "
                f"Remaining: {timedelta(seconds=int(remaining_time))}"
            )
    
    # Delete any remaining users without content
    bulk_delete_no_content_users()
    
    total_time = time.time() - start_time
    print(
        f"Deletion Complete: {processed_count:,} users deleted "
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