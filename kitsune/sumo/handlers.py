from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


class AbstractHandler(ABC):
    """Abstract base class for all handlers."""

    @abstractmethod
    def handle(self) -> None:
        pass


@dataclass
class AbstractChain(Generic[T]):
    """Abstract base class for a chain of handlers."""

    _handlers: list[T] = field(default_factory=list)

    @property
    def handlers(self) -> Sequence[T]:
        return self._handlers

    def add_handler(self, handler: T) -> None:
        """Add a handler to the chain."""
        self._handlers.append(handler)


class AccountHandler(AbstractHandler):
    """Handler for account-related tasks."""

    def handle(self) -> None:
        """Implementation of the generic handle method."""
        self.handle_account({})

    @abstractmethod
    def handle_account(self, data: dict) -> None:
        """Handler method specific to account tasks."""
        pass
