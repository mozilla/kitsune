from django.shortcuts import render

from tidings.models import Watch


def unsubscribe(request, watch_id):
    """Unsubscribe from (i.e. delete) the watch of ID ``watch_id``.

    Expects an ``s`` querystring parameter matching the watch's secret.

    GET will result in a confirmation page (or a failure page if the secret is
    wrong). POST will actually delete the watch (again, if the secret is
    correct).

    The templates assume use of the Jinja templating engine via jingo.Loader
    and the presence of a ``base.html`` template containing a ``content``
    block.

    If you aren't using Jinja via jingo.Loader, you can replace the templates
    with your own django templates.

    """
    # Grab the watch and secret; complain if either is wrong:
    try:
        watch = Watch.objects.get(pk=watch_id)
        secret = request.GET.get('s')  # 's' is for 'secret' but saves wrapping in mails
        if secret != watch.secret:
            raise Watch.DoesNotExist
    except Watch.DoesNotExist:
        return render(request, 'tidings/unsubscribe_error.html')

    if request.method == 'POST':
        watch.delete()
        return render(request, 'tidings/unsubscribe_success.html')

    return render(request, 'tidings/unsub.html', {
        'watch': watch})
