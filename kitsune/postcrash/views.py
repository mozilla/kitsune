from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.cache import cache_page

from kitsune.postcrash.models import Signature


@cache_page(60 * 60 * 24)  # One day.
def api(request):
    s = request.GET.get('s', None)
    if not s:
        return HttpResponseBadRequest(mimetype='text/plain')

    # Don't use get_object_or_404 so we can return a 404 with no content.
    try:
        sig = Signature.objects.get(signature=s)
    except Signature.DoesNotExist:
        return HttpResponse('', status=404, mimetype='text/plain')

    host = Site.objects.get_current()
    path = sig.get_absolute_url()
    return HttpResponse(u'https://%s%s' % (host, path), mimetype='text/plain')
