from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from kitsune.users.models import User


class UserDeletionListener(ABC):
    """
    Listener that is responsible for deleting a user.
    """

    @abstractmethod
    def on_user_deletion(self, user: User):
        pass


@dataclass
class UserDeletionPublisher:
    """
    Publisher that is responsible for publishing a user deletion event.
    """

    user: User
    listeners: list[UserDeletionListener] = field(default_factory=list)

    def register_listener(self, listener: UserDeletionListener) -> None:
        self.listeners.append(listener)

    def get_listeners(self) -> list[str]:
        return [listener.__class__.__name__ for listener in self.listeners]

    def publish(self):
        for listener in self.listeners:
            listener.on_user_deletion(self.user)
