from typing import Any

from pydantic import BaseModel

ADDITIONAL_FORMAT_INSTRUCTIONS = """

**Important**:
- All string values in the JSON **must** be valid JSON strings.
- **Escape any special characters** to ensure the final output is a valid JSON object. This includes, but is not limited to, double quotes (`"`), backslashes (`\\`), and control characters (e.g., `\\n`, `\\t`).
- For example, a raw string like `This is a "test".` must be formatted as `"This is a \"test\"."` or `"This is a 'test'."` in the final JSON string value.
"""

USER_CONTENT_TEMPLATE = """
# {subject}

{content}
"""


def model_to_dict(input: BaseModel) -> dict[str, Any]:
    """Convert a Pydantic BaseModel instance to a dict."""
    return input.model_dump()
