from kitsune import messages


def unread_message_count(request):
    """Adds the unread private messages count to the context.

    * Returns 0 for anonymous users.
    * Returns 0 if waffle flag is off.
    """
    count = 0
    if (hasattr(request, 'user') and request.user.is_authenticated()):
        count = messages.unread_count_for(request.user)
    return {'unread_message_count': count}
