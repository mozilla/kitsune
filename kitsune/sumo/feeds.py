from django.contrib.syndication.views import Feed as DjFeed


class Feed(DjFeed):
    """
    For some reason when running via the Meinheld WSGI worker for Gunicorn, the async
    nature of the response cycle doesn't properly handle responses that have more than
    one item in the `Response._container` list. This class squashes that list before
    returning the HttpResponse object.

    See https://github.com/mozilla/kitsune/issues/3017
    """

    def __call__(self, request, *args, **kwargs):
        response = super(Feed, self).__call__(request, *args, **kwargs)
        # this squashes the response._container list to a single item
        response.content = response.content
        return response
