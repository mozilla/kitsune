# Copyright 2008-2009 WebDriver committers
# Copyright 2008-2009 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import socket
import string

try:
    from urllib import request as url_request
except ImportError:
    import urllib2 as url_request

try:
    from urllib import parse
except ImportError:
    import urlparse as parse

from .command import Command
from .errorhandler import ErrorCode
from . import utils

LOGGER = logging.getLogger(__name__)


class Request(url_request.Request):
    """
    Extends the url_request.Request to support all HTTP request types.
    """

    def __init__(self, url, data=None, method=None):
        """
        Initialise a new HTTP request.

        :Args:
         - url - String for the URL to send the request to.
         - data - Data to send with the request.
        """
        if method is None:
            method = data is not None and 'POST' or 'GET'
        elif method != 'POST' and method != 'PUT':
            data = None
        self._method = method
        url_request.Request.__init__(self, url, data=data)

    def get_method(self):
        """
        Returns the HTTP method used by this request.
        """
        return self._method


class Response(object):
    """
    Represents an HTTP response.
    """

    def __init__(self, fp, code, headers, url):
        """
        Initialise a new Response.

        :Args:
         - fp - The response body file object.
         - code - The HTTP status code returned by the server.
         - headers - A dictionary of headers returned by the server.
         - url - URL of the retrieved resource represented by this Response.
        """
        self.fp = fp
        self.read = fp.read
        self.code = code
        self.headers = headers
        self.url = url

    def close(self):
        """
        Close the response body file object.
        """
        self.read = None
        self.fp = None

    def info(self):
        """
        Returns the response headers.
        """
        return self.headers

    def geturl(self):
        """
        Returns the URL for the resource returned in this response.
        """
        return self.url


class HttpErrorHandler(url_request.HTTPDefaultErrorHandler):
    """
    A custom HTTP error handler.

    Used to return Response objects instead of raising an HTTPError exception.
    """

    def http_error_default(self, req, fp, code, msg, headers):
        """
        Default HTTP error handler.

        :Args:
         - req - The original Request object.
         - fp - The response body file object.
         - code - The HTTP status code returned by the server.
         - msg - The HTTP status message returned by the server.
         - headers - The response headers.

        :Returns:
          A new Response object.
        """
        return Response(fp, code, headers, req.get_full_url())


class RemoteConnection(object):
    """
    A connection with the Remote WebDriver server.

    Communicates with the server using the WebDriver wire protocol:
    http://code.google.com/p/selenium/wiki/JsonWireProtocol
    """

    def __init__(self, remote_server_addr):
        # Attempt to resolve the hostname and get an IP address.
        parsed_url = parse.urlparse(remote_server_addr)
        if parsed_url.hostname:
            try:
                netloc = socket.gethostbyname(parsed_url.hostname)
                if parsed_url.port:
                    netloc += ':%d' % parsed_url.port
                if parsed_url.username:
                    auth = parsed_url.username
                    if parsed_url.password:
                        auth += ':%s' % parsed_url.password
                    netloc = '%s@%s' % (auth, netloc)
                remote_server_addr = parse.urlunparse(
                    (parsed_url.scheme, netloc, parsed_url.path,
                     parsed_url.params, parsed_url.query, parsed_url.fragment))
            except socket.gaierror:
                LOGGER.info('Could not get IP address for host: %s' %
                            parsed_url.hostname)

        self._url = remote_server_addr
        self._commands = {
            Command.NEW_SESSION: ('POST', '/session'),
            Command.QUIT: ('DELETE', '/session/$sessionId'),
            Command.GET_CURRENT_WINDOW_HANDLE:
                ('GET', '/session/$sessionId/window_handle'),
            Command.GET_WINDOW_HANDLES:
                ('GET', '/session/$sessionId/window_handles'),
            Command.GET: ('POST', '/session/$sessionId/url'),
            Command.GO_FORWARD: ('POST', '/session/$sessionId/forward'),
            Command.GO_BACK: ('POST', '/session/$sessionId/back'),
            Command.REFRESH: ('POST', '/session/$sessionId/refresh'),
            Command.EXECUTE_SCRIPT: ('POST', '/session/$sessionId/execute'),
            Command.GET_CURRENT_URL: ('GET', '/session/$sessionId/url'),
            Command.GET_TITLE: ('GET', '/session/$sessionId/title'),
            Command.GET_PAGE_SOURCE: ('GET', '/session/$sessionId/source'),
            Command.SCREENSHOT: ('GET', '/session/$sessionId/screenshot'),
            Command.SET_BROWSER_VISIBLE:
                ('POST', '/session/$sessionId/visible'),
            Command.IS_BROWSER_VISIBLE: ('GET', '/session/$sessionId/visible'),
            Command.FIND_ELEMENT: ('POST', '/session/$sessionId/element'),
            Command.FIND_ELEMENTS: ('POST', '/session/$sessionId/elements'),
            Command.GET_ACTIVE_ELEMENT:
                ('POST', '/session/$sessionId/element/active'),
            Command.FIND_CHILD_ELEMENT:
                ('POST', '/session/$sessionId/element/$id/element'),
            Command.FIND_CHILD_ELEMENTS:
                ('POST', '/session/$sessionId/element/$id/elements'),
            Command.CLICK_ELEMENT: ('POST', '/session/$sessionId/element/$id/click'),
            Command.CLEAR_ELEMENT: ('POST', '/session/$sessionId/element/$id/clear'),
            Command.SUBMIT_ELEMENT: ('POST', '/session/$sessionId/element/$id/submit'),
            Command.GET_ELEMENT_TEXT: ('GET', '/session/$sessionId/element/$id/text'),
            Command.SEND_KEYS_TO_ELEMENT:
                ('POST', '/session/$sessionId/element/$id/value'),
            Command.SEND_KEYS_TO_ACTIVE_ELEMENT:
                ('POST', '/session/$sessionId/keys'),
            Command.UPLOAD_FILE: ('POST', "/session/$sessionId/file"),
            Command.GET_ELEMENT_VALUE:
                ('GET', '/session/$sessionId/element/$id/value'),
            Command.GET_ELEMENT_TAG_NAME:
                ('GET', '/session/$sessionId/element/$id/name'),
            Command.IS_ELEMENT_SELECTED:
                ('GET', '/session/$sessionId/element/$id/selected'),
            Command.SET_ELEMENT_SELECTED:
                ('POST', '/session/$sessionId/element/$id/selected'),
            Command.TOGGLE_ELEMENT:
                ('POST', '/session/$sessionId/element/$id/toggle'),
            Command.IS_ELEMENT_ENABLED:
                ('GET', '/session/$sessionId/element/$id/enabled'),
            Command.IS_ELEMENT_DISPLAYED:
                ('GET', '/session/$sessionId/element/$id/displayed'),
            Command.HOVER_OVER_ELEMENT:
                ('POST', '/session/$sessionId/element/$id/hover'),
            Command.GET_ELEMENT_LOCATION:
                ('GET', '/session/$sessionId/element/$id/location'),
            Command.GET_ELEMENT_LOCATION_ONCE_SCROLLED_INTO_VIEW:
                ('GET', '/session/$sessionId/element/$id/location_in_view'),
            Command.GET_ELEMENT_SIZE:
                ('GET', '/session/$sessionId/element/$id/size'),
            Command.GET_ELEMENT_ATTRIBUTE:
                ('GET', '/session/$sessionId/element/$id/attribute/$name'),
            Command.ELEMENT_EQUALS:
                ('GET', '/session/$sessionId/element/$id/equals/$other'),
            Command.GET_ALL_COOKIES: ('GET', '/session/$sessionId/cookie'),
            Command.ADD_COOKIE: ('POST', '/session/$sessionId/cookie'),
            Command.DELETE_ALL_COOKIES:
                ('DELETE', '/session/$sessionId/cookie'),
            Command.DELETE_COOKIE:
                ('DELETE', '/session/$sessionId/cookie/$name'),
            Command.SWITCH_TO_FRAME: ('POST', '/session/$sessionId/frame'),
            Command.SWITCH_TO_WINDOW: ('POST', '/session/$sessionId/window'),
            Command.CLOSE: ('DELETE', '/session/$sessionId/window'),
            Command.DRAG_ELEMENT:
                ('POST', '/session/$sessionId/element/$id/drag'),
            Command.GET_SPEED: ('GET', '/session/$sessionId/speed'),
            Command.SET_SPEED: ('POST', '/session/$sessionId/speed'),
            Command.GET_ELEMENT_VALUE_OF_CSS_PROPERTY:
                ('GET',  '/session/$sessionId/element/$id/css/$propertyName'),
            Command.IMPLICIT_WAIT:
                ('POST', '/session/$sessionId/timeouts/implicit_wait'),
            Command.EXECUTE_ASYNC_SCRIPT: ('POST','/session/$sessionId/execute_async'),
            Command.SET_SCRIPT_TIMEOUT:
                ('POST', '/session/$sessionId/timeouts/async_script'),
            Command.SET_TIMEOUTS:
                ('POST', '/session/$sessionId/timeouts'),
            Command.DISMISS_ALERT:
                ('POST', '/session/$sessionId/dismiss_alert'),
            Command.ACCEPT_ALERT:
                ('POST', '/session/$sessionId/accept_alert'),
            Command.SET_ALERT_VALUE:
                ('POST', '/session/$sessionId/alert_text'),
            Command.GET_ALERT_TEXT:
                ('GET', '/session/$sessionId/alert_text'),
            Command.CLICK:
                ('POST', '/session/$sessionId/click'),
            Command.DOUBLE_CLICK:
                ('POST', '/session/$sessionId/doubleclick'),
            Command.MOUSE_DOWN:
                ('POST', '/session/$sessionId/buttondown'),
            Command.MOUSE_UP:
                ('POST', '/session/$sessionId/buttonup'),
            Command.MOVE_TO:
                ('POST', '/session/$sessionId/moveto'),
            Command.GET_WINDOW_SIZE:
                ('GET', '/session/$sessionId/window/$windowHandle/size'),
            Command.SET_WINDOW_SIZE:
                ('POST', '/session/$sessionId/window/$windowHandle/size'),
            Command.GET_WINDOW_POSITION:
                ('GET', '/session/$sessionId/window/$windowHandle/position'),
            Command.SET_WINDOW_POSITION:
                ('POST', '/session/$sessionId/window/$windowHandle/position'),
            Command.MAXIMIZE_WINDOW:
                ('POST', '/session/$sessionId/window/$windowHandle/maximize'),
            Command.SET_SCREEN_ORIENTATION:
                ('POST', '/session/$sessionId/orientation'),
            Command.GET_SCREEN_ORIENTATION:
                ('GET', '/session/$sessionId/orientation'),
            Command.SINGLE_TAP:
                ('POST', '/session/$sessionId/touch/click'),
            Command.TOUCH_DOWN:
                ('POST', '/session/$sessionId/touch/down'),
            Command.TOUCH_UP:
                ('POST', '/session/$sessionId/touch/up'),
            Command.TOUCH_MOVE:
                ('POST', '/session/$sessionId/touch/move'),
            Command.TOUCH_SCROLL:
                ('POST', '/session/$sessionId/touch/scroll'),
            Command.DOUBLE_TAP:
                ('POST', '/session/$sessionId/touch/doubleclick'),
            Command.LONG_PRESS:
                ('POST', '/session/$sessionId/touch/longclick'),
            Command.FLICK:
                ('POST', '/session/$sessionId/touch/flick'),
            Command.EXECUTE_SQL:
                ('POST', '/session/$sessionId/execute_sql'),
            Command.GET_LOCATION:
                ('GET', '/session/$sessionId/location'),
            Command.SET_LOCATION:
                ('POST', '/session/$sessionId/location'),
            Command.GET_APP_CACHE:
                ('GET', '/session/$sessionId/application_cache'),
            Command.GET_APP_CACHE_STATUS:
                ('GET', '/session/$sessionId/application_cache/status'),
            Command.CLEAR_APP_CACHE:
                ('DELETE', '/session/$sessionId/application_cache/clear'),
            Command.IS_BROWSER_ONLINE:
                ('GET', '/session/$sessionId/browser_connection'),
            Command.SET_BROWSER_ONLINE:
                ('POST', '/session/$sessionId/browser_connection'),
            Command.GET_LOCAL_STORAGE_ITEM:
                ('GET', '/session/$sessionId/local_storage/key/$key'),
            Command.REMOVE_LOCAL_STORAGE_ITEM:
                ('POST', '/session/$sessionId/local_storage/key/$key'),
            Command.GET_LOCAL_STORAGE_KEYS:
                ('GET', '/session/$sessionId/local_storage'),
            Command.SET_LOCAL_STORAGE_ITEM:
                ('POST', '/session/$sessionId/local_storage'),
            Command.CLEAR_LOCAL_STORAGE:
                ('DELETE', '/session/$sessionId/local_storage'),
            Command.GET_LOCAL_STORAGE_SIZE:
                ('GET', '/session/$sessionId/local_storage/size'),
            Command.GET_SESSION_STORAGE_ITEM:
                ('GET', '/session/$sessionId/session_storage/key/$key'),
            Command.REMOVE_SESSION_STORAGE_ITEM:
                ('DELETE', '/session/$sessionId/session_storage/key/$key'),
            Command.GET_SESSION_STORAGE_KEYS:
                ('GET', '/session/$sessionId/session_storage'),
            Command.SET_SESSION_STORAGE_ITEM:
                ('POST', '/session/$sessionId/session_storage'),
            Command.CLEAR_SESSION_STORAGE:
                ('DELETE', '/session/$sessionId/session_storage'),
            Command.GET_SESSION_STORAGE_SIZE:
                ('GET','/session/$sessionId/session_storage/size'),
            Command.GET_LOG:
                ('POST','/session/$sessionId/log'),
            Command.GET_AVAILABLE_LOG_TYPES:
                ('GET','/session/$sessionId/log/types'),
            }

    def execute(self, command, params):
        """
        Send a command to the remote server.

        Any path subtitutions required for the URL mapped to the command should be
        included in the command parameters.

        :Args:
         - command - A string specifying the command to execute.
         - params - A dictionary of named parameters to send with the command as
           its JSON payload.
        """
        command_info = self._commands[command]
        assert command_info is not None, 'Unrecognised command %s' % command
        data = utils.dump_json(params)
        path = string.Template(command_info[1]).substitute(params)
        url = '%s%s' % (self._url, path)
        return self._request(url, method=command_info[0], data=data)

    def _request(self, url, data=None, method=None):
        """
        Send an HTTP request to the remote server.

        :Args:
         - method - A string for the HTTP method to send the request with.
         - url - The URL to send the request to.
         - body - The message body to send.

        :Returns:
          A dictionary with the server's parsed JSON response.
        """
        LOGGER.debug('%s %s %s' % (method, url, data))

        parsed_url = parse.urlparse(url)
        password_manager = None
        if parsed_url.username:
            netloc = parsed_url.hostname
            if parsed_url.port:
                netloc += ":%s" % parsed_url.port
            cleaned_url = parse.urlunparse((parsed_url.scheme,
                                               netloc,
                                               parsed_url.path,
                                               parsed_url.params,
                                               parsed_url.query,
                                               parsed_url.fragment))
            password_manager = url_request.HTTPPasswordMgrWithDefaultRealm()
            password_manager.add_password(None,
                                          "%s://%s" % (parsed_url.scheme, netloc),
                                          parsed_url.username,
                                          parsed_url.password)
            request = Request(cleaned_url, data=data.encode('utf-8'), method=method)
        else:
            request = Request(url, data=data.encode('utf-8'), method=method)

        request.add_header('Accept', 'application/json')
        request.add_header('Content-Type', 'application/json;charset=UTF-8')

        if password_manager:
            opener = url_request.build_opener(url_request.HTTPRedirectHandler(),
                                          HttpErrorHandler(),
                                          url_request.HTTPBasicAuthHandler(password_manager))
        else:
            opener = url_request.build_opener(url_request.HTTPRedirectHandler(),
                                          HttpErrorHandler())
        response = opener.open(request)
        try:
            if response.code > 399 and response.code < 500:
                return {'status': response.code, 'value': response.read()}
            body = response.read().decode('utf-8').replace('\x00', '').strip()
            content_type = [value for name, value in response.info().items() if name.lower() == "content-type"]
            if not any([x.startswith('image/png') for x in content_type]):
                try:
                    data = utils.load_json(body.strip())
                except ValueError:
                    if response.code > 199 and response.code < 300:
                        status = ErrorCode.SUCCESS
                    else:
                        status = ErrorCode.UNKNOWN_ERROR
                    return {'status': status, 'value': body.strip()}

                assert type(data) is dict, (
                    'Invalid server response body: %s' % body)
                assert 'status' in data, (
                    'Invalid server response; no status: %s' % body)
                # Some of the drivers incorrectly return a response
                # with no 'value' field when they should return null.
                if 'value' not in data:
                    data['value'] = None
                return data
            else:
                data = {'status': 0, 'value': body.strip()}
                return data
        finally:
            response.close()
