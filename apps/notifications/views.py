import jingo

from notifications.models import Watch


def unsubscribe(request, watch_id):
    """Unsubscribe from (i.e. delete) a Watch."""
    # Grab the watch and secret; complain if either is wrong:
    try:
        watch = Watch.objects.get(pk=watch_id)
        secret = request.GET.get('s')  # 's' is for 'secret' but saves wrapping
                                       # in mails
        if secret != watch.secret:
            raise Watch.DoesNotExist
    except Watch.DoesNotExist:
        return jingo.render(request, 'notifications/unsubscribe_error.html')

    if request.method == 'POST':
        watch.delete()
        return jingo.render(request, 'notifications/unsubscribe_success.html')

    return jingo.render(request, 'notifications/unsubscribe.html')
