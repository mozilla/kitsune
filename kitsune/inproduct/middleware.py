class EuBuildMiddleware(object):
    """EU Ballot Firefox builds mangle inproduct URLs.

    EU Ballot builds of Firefox add a /eu/ component to the incoming URL
    from in-product help links. Unfortunately, they add it in the middle:

        /1/<product>/<version>/<platform>/<locale>/eu/<optional-topic>

    Handling that in regex is tricky and really complicates the view. So
    we just remove that part of the URL and annotate the request so the
    view knows to add the ?eu=1 query string parameter.

    """

    def process_request(self, request):
        path = request.path_info.lstrip('/')
        if path.startswith('1/'):
            parts = path.split('/')
            if len(parts) >= 6 and parts[5] == 'eu':
                request.eu_build = True
                del parts[5]
                path = '/'.join(parts)

            request.path_info = '/' + path
