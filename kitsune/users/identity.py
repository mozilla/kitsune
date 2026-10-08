import hashlib
from collections.abc import Iterator
from contextlib import contextmanager

from django.db import connection, transaction


@contextmanager
def lock_account_email(email: str) -> Iterator[None]:
    """Serialize account creation and email changes for a normalized address."""
    normalized_email = email.strip().casefold()
    digest = hashlib.sha256(f"sumo-account-email:{normalized_email}".encode()).digest()
    lock_id = int.from_bytes(digest[:8], byteorder="big", signed=True)
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_id])
        yield
