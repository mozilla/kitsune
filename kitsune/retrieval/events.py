"""A small, shared boundary for retrieval's structured log events.

The helper rejects obvious sensitive field names and payload-shaped values. It cannot infer
the meaning of arbitrary names, so each emitting seam still tests its actual event fields.
"""

import logging
from collections.abc import Mapping

log = logging.getLogger("k.retrieval")

_MAX_VALUE_LENGTH = 200

_SENSITIVE_FIELDS = {
    "access_group_ids",
    "content",
    "content_text",
    "content_vector",
    "credentials",
    "group_ids",
    "groups",
    "html",
    "keywords",
    "password",
    "restrict_to_groups",
    "secret",
    "summary",
    "text",
    "title",
    "token",
    "vector",
    "vectors",
}
# Keep this aligned with the logging runtime rather than copying LogRecord's field list.
_RESERVED_FIELDS = set(logging.makeLogRecord({}).__dict__) | {"asctime", "message"}


class UnsafeEventField(ValueError):
    """An event field is explicitly sensitive, reserved, or payload-shaped."""


def _safe_value(name: str, value, *, nested: bool = False):
    if name in _SENSITIVE_FIELDS:
        raise UnsafeEventField(f"event field {name!r} may carry sensitive content")
    if isinstance(value, str):
        return value if len(value) <= _MAX_VALUE_LENGTH else value[:_MAX_VALUE_LENGTH] + "…"
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, Mapping) and not nested:
        return {str(key): _safe_value(str(key), item, nested=True) for key, item in value.items()}
    raise UnsafeEventField(
        f"event field {name!r} must be a scalar or one flat mapping, not {type(value).__name__}"
    )


def emit(event: str, *, level: int = logging.INFO, **fields) -> None:
    """Record one stable event name with bounded scalar fields."""
    if not isinstance(event, str) or not event:
        raise ValueError("event must be a non-empty string")
    for name in fields:
        if name in _RESERVED_FIELDS:
            raise UnsafeEventField(f"event field {name!r} is reserved by logging")

    log.log(level, event, extra={name: _safe_value(name, value) for name, value in fields.items()})
