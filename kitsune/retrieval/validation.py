"""Shared validation predicates for retrieval's defensive boundaries.

Predicates only name the checks; each caller keeps its own exception type and
message so every boundary still raises its native error.
"""

import math
from typing import TypeGuard


def is_int(value: object) -> TypeGuard[int]:
    """An actual int; bools are excluded even though bool subclasses int."""
    return isinstance(value, int) and not isinstance(value, bool)


def is_positive_int(value: object) -> TypeGuard[int]:
    return is_int(value) and value > 0


def is_nonnegative_int(value: object) -> TypeGuard[int]:
    return is_int(value) and value >= 0


def is_finite_number(value: object) -> TypeGuard[int | float]:
    """A finite int or float; bools and nan/inf are excluded."""
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)
