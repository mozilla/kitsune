import time
from datetime import timedelta

from django.db import migrations
from django.db.models import Q


def delete_non_migrated_users(apps, schema_editor):
    """
    Delete users where is_fxa_migrated is False and who aren't creators/owners/users of
    any content.
    """
    User = apps.get_model("auth", "User")
    users_to_delete = User.objects.filter(profile__is_fxa_migrated=False).exclude(
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

    total_users = users_to_delete.count()
    if total_users == 0:
        print("No users to delete")
        return

    print(f"Starting deletion of {total_users:,} users")
    start_time = time.time()
    deleted_count = 0
    batch_size = 2000

    user_ids = users_to_delete.values_list("id", flat=True).iterator(chunk_size=batch_size)
    current_batch = []

    for user_id in user_ids:
        current_batch.append(user_id)

        if len(current_batch) >= batch_size:
            # Delete the batch using _base_manager to avoid the overridden managers
            # of each model through the cascade.
            # We don't care about the extra logic b/c the accounts that are being deleted are empty
            deletion_counts = User._base_manager.filter(id__in=current_batch).delete()
            # get the user, not the cascaded deletes
            user_deletes = deletion_counts[1].get("auth.User", 0)
            deleted_count += user_deletes
            current_batch = []

            elapsed_time = time.time() - start_time
            avg_time_per_user = elapsed_time / deleted_count if deleted_count > 0 else 0
            current_rate = deleted_count / elapsed_time * 60 if elapsed_time > 0 else 0
            remaining_time = (
                (total_users - deleted_count) * avg_time_per_user if deleted_count > 0 else 0
            )

            print(
                f"""
                Progress Report:
                ---------------
                Users Deleted: {deleted_count:,} of {total_users:,} ({(deleted_count/total_users*100):.1f}%)
                Elapsed Time: {timedelta(seconds=int(elapsed_time))}
                Average Time per User: {avg_time_per_user:.3f} seconds
                Current Rate: {current_rate:.1f} users/minute
                Estimated Time Remaining: {timedelta(seconds=int(remaining_time))}
                """
            )

    if current_batch:
        deletion_counts = User._base_manager.filter(id__in=current_batch).delete()
        user_deletes = deletion_counts[1].get("auth.User", 0)
        deleted_count += user_deletes

    total_time = time.time() - start_time
    print(
        f"""
        Deletion Complete:
        -----------------
        Total Users Deleted: {deleted_count:,} of {total_users:,}
        Total Time: {timedelta(seconds=int(total_time))}
        Average Time per User: {(total_time/deleted_count if deleted_count > 0 else 0):.3f} seconds
        Overall Rate: {(deleted_count/total_time*60 if total_time > 0 else 0):.1f} users/minute
        """
    )


def reverse_migration(apps, schema_editor):
    """
    No reverse migration possible since deletion cannot be undone
    """
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0033_delete_old_account_events"),
    ]

    operations = [
        migrations.RunPython(
            delete_non_migrated_users,
            reverse_migration,
        ),
    ]
