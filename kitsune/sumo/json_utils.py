import json
import re

from django.http import HttpResponse
from django.utils.translation import ugettext as _

from kitsune.sumo.api_utils import JSONRenderer


def template_json(data):
    """Returns json as a str

    Normally json is rendered as bytes, but putting bytes in a template that
    is itself encoded to bytes causes problems when trying to re-read the
    json from the template (with javascript).

    :arg data: the data to jsonify.

    :returns: str
    """
    return JSONRenderer().render(data).decode()


def jsonp_is_valid(funcname):
    """Returns whether the jsonp function name is valid

    :arg funcname: the name of the jsonp function

    :returns: True or False

    """
    func_regex = re.compile(
        r"""
        ^[a-zA-Z_\$]
        [a-zA-Z0-9_\$]*
        (\[[a-zA-Z0-9_\$]*\])*
        (\.[a-zA-Z0-9_\$]+
            (\[[a-zA-Z0-9_\$]*\])*
        )*$
    """,
        re.VERBOSE,
    )
    return bool(func_regex.match(funcname))


def markup_json(view_fun):
    """Marks up the request object with JSON bits

    * ``IS_JSON``: whether or not this is a json request
    * ``JSON_CALLBACK``: the json callback function to wrap with
    * ``CONTENT_TYPE``: the content type to return

    Further, this verifies the ``JSON_CALLBACK`` if there is one and if it's not
    valid, it returns an error response.

    """

    def _markup_json(request, *args, **kwargs):
        request.IS_JSON = request.GET.get("format") == "json"
        if request.IS_JSON:
            request.JSON_CALLBACK = request.GET.get("callback", "").strip()
        else:
            request.JSON_CALLBACK = ""
        if request.IS_JSON:
            request.CONTENT_TYPE = (
                "application/x-javascript" if request.JSON_CALLBACK else "application/json"
            )
        else:
            request.CONTENT_TYPE = "text/html"

        # Check callback is valid
        if request.JSON_CALLBACK and not jsonp_is_valid(request.JSON_CALLBACK):
            return HttpResponse(
                json.dumps({"error": _("Invalid callback function.")}),
                content_type=request.CONTENT_TYPE,
                status=400,
            )

        return view_fun(request, *args, **kwargs)

    return _markup_json
