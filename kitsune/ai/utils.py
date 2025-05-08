from functools import wraps
from typing import Any
import threading

from django.db import connection
from langchain_core.messages import AIMessage


def has_tool_been_called(tool_name: str, response: dict[str, Any]) -> bool:
    """
    Given the name of a tool and the response of an agent, determines whether
    or not the agent called the tool.
    """
    return any(
        isinstance(msg, AIMessage) and any(tc.get("name") == tool_name for tc in msg.tool_calls)
        for msg in response["messages"]
    )


def close_db_connection_when_done(func):
    """
    Decorator that closes Django's default database connection when the function
    has completed, but only if the function is not running within the main thread.
    When an agent created by `create_react_agent` makes a tool call, the tool is
    run within a thread pool. If the tool connects to the database, the connection
    within its thread remains even after the tool has completed. Use this decorator
    to ensure that the default database connection is closed when the tool completes.
    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            if threading.current_thread() is not threading.main_thread():
                connection.close()

    return wrapped
