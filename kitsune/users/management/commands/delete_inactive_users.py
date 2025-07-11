from datetime import timedelta
import time

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.db import DatabaseError, IntegrityError
from django.utils import timezone
from django.contrib.auth import get_user_model

from kitsune.users.utils import delete_user_pipeline


class Command(BaseCommand):
    help = "Delete users who haven't logged in for a specified period (default: 3 years)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--years",
            type=int,
            default=3,
            help="Number of years of inactivity before deletion (default: 3)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Batch size for bulk operations (default: 1000)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )
        parser.add_argument(
            "--progress-interval",
            type=int,
            default=1000,
            help="How often to report progress (default: every 1000 users)",
        )
        parser.add_argument(
            "--cutoff-date",
            type=str,
            help="Specific cutoff date in YYYY-MM-DD format (overrides --years)",
        )

    def handle(self, *args, **options):
        if options["cutoff_date"]:
            try:
                cutoff_date = timezone.datetime.strptime(
                    options["cutoff_date"], "%Y-%m-%d"
                ).replace(tzinfo=timezone.utc)
            except ValueError:
                raise CommandError("Invalid date format. Use YYYY-MM-DD")
        else:
            cutoff_date = timezone.now() - timedelta(days=options["years"] * 365)

        self.stdout.write(f"Looking for users inactive since: {cutoff_date}")

        if options["dry_run"]:
            self._find_and_delete_users(cutoff_date, options, dry_run=True)
            return

        self._find_and_delete_users(cutoff_date, options, dry_run=False)

    def _find_and_delete_users(self, cutoff_date, options: dict, dry_run: bool = False):
        User = get_user_model()
        processed_count = 0
        pipeline_count = 0
        direct_count = 0
        error_count = 0
        batch_size = options["batch_size"]
        progress_interval = options["progress_interval"]

        start_time = time.time()

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

        users_with_content = User.objects.filter(last_login__lt=cutoff_date).filter(
            has_content_criteria
        )
        users_without_content = User.objects.filter(last_login__lt=cutoff_date).exclude(
            has_content_criteria
        )
        content_count = users_with_content.count()
        no_content_count = users_without_content.count()
        total_users = content_count + no_content_count

        if total_users == 0:
            self.stdout.write("No inactive users found to delete")
            return

        self.stdout.write(
            self.style.WARNING(
                f"Found {total_users:,} inactive users for deletion:\n"
                f"  Users with content: {content_count:,} (will use delete_user_pipeline)\n"
                f"  Users without content: {no_content_count:,} (will use bulk delete)"
            )
        )

        if dry_run:
            self.stdout.write(self.style.SUCCESS("DRY RUN: No users were actually deleted"))
            return

        self.stdout.write(
            self.style.SUCCESS(f"Starting deletion of {total_users:,} inactive users")
        )

        # Process users without content using bulk delete
        self.stdout.write("Processing users without content using bulk delete...")

        users_no_content_batch = []
        for user in users_without_content.iterator(chunk_size=batch_size):
            users_no_content_batch.append(user.id)

            if len(users_no_content_batch) >= batch_size:
                batch_direct_count, batch_error_count = self._bulk_delete_batch(
                    User, users_no_content_batch
                )
                direct_count += batch_direct_count
                error_count += batch_error_count
                users_no_content_batch.clear()

            processed_count += 1

            if processed_count % progress_interval == 0:
                self._report_progress(
                    processed_count,
                    total_users,
                    pipeline_count,
                    direct_count,
                    error_count,
                    start_time,
                )
        if users_no_content_batch:
            batch_direct_count, batch_error_count = self._bulk_delete_batch(
                User, users_no_content_batch
            )
            direct_count += batch_direct_count
            error_count += batch_error_count

        # Process users with content using delete_user_pipeline
        self.stdout.write("Processing users with content using delete_user_pipeline...")

        for user in users_with_content.iterator(chunk_size=batch_size):
            try:
                delete_user_pipeline(user)
                pipeline_count += 1
            except (DatabaseError, IntegrityError) as e:
                error_count += 1
                self.stderr.write(f"Error deleting user {user.id}: {e}")

            processed_count += 1

            if processed_count % progress_interval == 0:
                self._report_progress(
                    processed_count,
                    total_users,
                    pipeline_count,
                    direct_count,
                    error_count,
                    start_time,
                )
        total_time = time.time() - start_time
        success_count = pipeline_count + direct_count

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDeletion Complete!\n"
                f"  Successfully deleted: {success_count:,} users\n"
                f"  Pipeline deletions: {pipeline_count:,}\n"
                f"  Bulk deletions: {direct_count:,}\n"
                f"  Errors: {error_count:,}\n"
                f"  Total time: {timedelta(seconds=int(total_time))}"
            )
        )

        if error_count > 0:
            self.stderr.write(
                self.style.WARNING(
                    f"Warning: {error_count} users could not be deleted. "
                    "Check error messages above."
                )
            )

    def _bulk_delete_batch(self, User, user_ids):
        _, deleted_objects = User.objects.filter(id__in=user_ids).delete()

        try:
            user_count = deleted_objects.get("auth.User", 0)
            return user_count, 0
        except (DatabaseError, IntegrityError) as e:
            self.stderr.write(f"Error batch deleting users: {e}")
            return 0, len(user_ids)

    def _report_progress(
        self,
        processed: int,
        total: int,
        pipeline: int,
        direct: int,
        errors: int,
        start_time: float,
    ):
        elapsed_time = time.time() - start_time
        progress_pct = processed / total * 100
        current_rate = (processed / elapsed_time * 60) if elapsed_time > 0 else 0

        self.stdout.write(
            f"Progress: {processed:,}/{total:,} ({progress_pct:.1f}%) | "
            f"Pipeline: {pipeline:,} | Direct: {direct:,} | Errors: {errors:,} | "
            f"Rate: {current_rate:.1f} users/min"
        )
