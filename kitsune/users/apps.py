import logging
import traceback

from django.apps import AppConfig

logger = logging.getLogger("k.security")


class UserConfig(AppConfig):
    name = "kitsune.users"
    label = "users"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from django.contrib.auth.models import User

        from kitsune.users.managers import RegularUserManager

        User.all_users = User.objects

        # Create and initialize the new manager
        new_manager = RegularUserManager()
        new_manager.model = User

        # Check if the original manager has a database specified
        if hasattr(User.all_users, "_db") and User.all_users._db is not None:
            new_manager._db = User.all_users._db

        if hasattr(User.all_users, "_hints"):
            new_manager._hints = User.all_users._hints
        User.objects = new_manager

        # Add runtime monitoring for user.groups.all() access  # noqa: group-leak
        self._add_groups_monitoring(User)

    def _add_groups_monitoring(self, User):
        """Add logging when user.groups.all() is called from views/templates."""  # noqa: group-leak
        from django.db.models.manager import BaseManager

        # Store original all() method from BaseManager
        _original_all = BaseManager.all

        # Cache for file line checks (file_path:line_no -> has_noqa)
        _noqa_cache = {}

        def monitored_all(self):
            """Wrapped all() that logs warnings when called from views/templates"""
            # Only monitor in development (DEBUG and DEV both enabled)
            from django.conf import settings
            if not (settings.DEBUG and settings.DEV):
                return _original_all(self)

            # Check if this is user.groups manager
            is_user_groups = (
                hasattr(self, "model")
                and self.model.__name__ == "Group"
                and hasattr(self, "instance")
                and isinstance(self.instance, User)
            )

            if is_user_groups:
                # Check if we're in a view/template context
                stack = traceback.extract_stack()
                suspicious_frames = [
                    frame
                    for frame in stack
                    if ("views.py" in frame.filename or "jinja2" in frame.filename)
                    and "admin" not in frame.filename
                    and "apps.py" not in frame.filename
                ]

                if suspicious_frames:
                    frame = suspicious_frames[0]  # Get first suspicious frame

                    # Check cache first
                    cache_key = f"{frame.filename}:{frame.lineno}"
                    has_noqa = _noqa_cache.get(cache_key)

                    if has_noqa is None:
                        # Not in cache, check the file
                        try:
                            with open(frame.filename) as f:
                                lines = f.readlines()
                                if frame.lineno <= len(lines):
                                    line = lines[frame.lineno - 1]
                                    has_noqa = '# noqa: group-leak' in line
                                else:
                                    has_noqa = False
                        except OSError:
                            # If we can't read the file, assume not safe
                            has_noqa = False

                        # Cache the result
                        _noqa_cache[cache_key] = has_noqa

                    # Only log warning if not marked safe
                    if not has_noqa:
                        RED_BG = "\033[41m\033[97m"
                        RESET = "\033[0m"
                        logger.warning(
                            f"{RED_BG}SECURITY{RESET}: user.groups.all() called from %s:%s. "  # noqa: group-leak
                            "Use profile.visible_group_profiles() instead to respect GroupProfile visibility. "
                            f"Add '{RED_BG}# noqa: group-leak{RESET}' if this is intentional.",
                            frame.filename,
                            frame.lineno,
                        )

            # Call original all()
            return _original_all(self)

        # Monkey-patch BaseManager.all globally
        BaseManager.all = monitored_all
