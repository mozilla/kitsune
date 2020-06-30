from django.apps import AppConfig


default_app_config = "kitsune.messages.MessagesConfig"


class MessagesConfig(AppConfig):
    name = "kitsune.messages"
    label = "kitsune_messages"


# The number of threads per page.
MESSAGES_PER_PAGE = 20
