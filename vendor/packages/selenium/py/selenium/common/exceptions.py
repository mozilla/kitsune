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

"""
Exceptions that may happen in all the webdriver code.
"""

class WebDriverException(Exception):
    """
    Base webdriver exception.
    """

    def __init__(self, msg=None, screen=None, stacktrace=None):
        self.msg = msg
        self.screen = screen
        self.stacktrace = stacktrace

    def __str__(self):
        exception_msg = "Message: %s " % repr(self.msg)
        if self.screen is not None:
            exception_msg = "%s; Screenshot: available via screen " \
                % exception_msg
        if self.stacktrace is not None:
            exception_msg = "%s; Stacktrace: %s " \
                % (exception_msg, str("\n" + "\n".join(self.stacktrace)))
        return exception_msg

class ErrorInResponseException(WebDriverException):
    """
    Thrown when an error has occurred on the server side.

    This may happen when communicating with the firefox extension
    or the remote driver server.
    """
    def __init__(self, response, msg):
        WebDriverException.__init__(self, msg)
        self.response = response

class InvalidSwitchToTargetException(WebDriverException):
    """
    Thrown when frame or window target to be switched doesn't exist.
    """
    pass

class NoSuchFrameException(InvalidSwitchToTargetException):
    """
    Thrown when frame target to be switched doesn't exist.
    """
    pass

class NoSuchWindowException(InvalidSwitchToTargetException):
    """
    Thrown when window target to be switched doesn't exist.

    To find the current set of active window handles, you can get a list 
    of the active window handles in the following way::

        print driver.window_handles

    """
    pass

class NoSuchElementException(WebDriverException):
    """
    Thrown when element could not be found.

    If you encounter this exception, you may want to check the following:
        * Check your selector used in your find_by...
        * Element may not yet be on the screen at the time of the find operation,
        (webpage is still loading) see selenium.webdriver.support.wait.WebDriverWait() 
        for how to write a wait wrapper to wait for an element to appear.
    """
    pass

class NoSuchAttributeException(WebDriverException):
    """
    Thrown when the attribute of element could not be found.

    You may want to check if the attribute exists in the particular browser you are 
    testing against.  Some browsers may have different property names for the same 
    property.  (IE8's .innerText vs. Firefox .textContent)
    """
    pass

class StaleElementReferenceException(WebDriverException):
    """
    Thrown when a reference to an element is now "stale".

    Stale means the element no longer appears on the DOM of the page.


    Possible causes of StaleElementReferenceException include, but not limited to:
        * You are no longer on the same page, or the page may have refreshed since the element 
        was located.
        * The element may have been removed and re-added to the screen, since it was located.
        Such as an element being relocated. 
        This can happen typically with a javascript framework when values are updated and the 
        node is rebuilt.
        * Element may have been inside an iframe or another context which was refreshed.
    """
    pass

class InvalidElementStateException(WebDriverException):  
    """
    """
    pass

class UnexpectedAlertPresentException(WebDriverException):
    """
    Thrown when an unexpected alert is appeared.
    
    Usually raised when when an expected modal is blocking webdriver form executing any 
    more commands.
    """
    pass

class NoAlertPresentException(WebDriverException):
    """
    Thrown when switching to no presented alert.

    This can be caused by calling an operation on the Alert() class when an alert is 
    not yet on the screen.
    """
    pass

class ElementNotVisibleException(InvalidElementStateException):
    """
    Thrown when an element is present on the DOM, but  
    it is not visible, and so is not able to be interacted with.

    Most commonly encountered when trying to click or read text 
    of an element that is hidden from view.
    """
    pass

class ElementNotSelectableException(InvalidElementStateException):
    """
    Thrown when trying to select an unselectable element.
    
    For example, selecting a 'script' element.
    """
    pass

class InvalidCookieDomainException(WebDriverException):
    """
    Thrown when attempting to add a cookie under a different domain
    than the current URL.
    """
    pass

class UnableToSetCookieException(WebDriverException):
    """
    Thrown when a driver fails to set a cookie.
    """
    pass

class RemoteDriverServerException(WebDriverException):
    """
    """
    pass

class TimeoutException(WebDriverException):
    """
    Thrown when a command does not complete in enough time.
    """
    pass

class MoveTargetOutOfBoundsException(WebDriverException):
    """
    Thrown when the target provided to the `ActionsChains` move() 
    method is invalid, i.e. out of document.
    """
    pass

class UnexpectedTagNameException(WebDriverException):
    """
    Thrown when a support class did not get an expected web element.
    """
    pass

class InvalidSelectorException(NoSuchElementException):
    """
    Thrown when the selector which is used to find an element does not return
    a WebElement. Currently this only happens when the selector is an xpath
    expression and it is either syntactically invalid (i.e. it is not a
    xpath expression) or the expression does not select WebElements
    (e.g. "count(//input)").
    """
    pass

class ImeNotAvailableException(WebDriverException):
    """
    Thrown when IME support is not available. This exception is thrown for every IME-related
    method call if IME support is not available on the machine.
    """
    pass

class ImeActivationFailedException(WebDriverException):
    """
    Thrown when activating an IME engine has failed.
    """
    pass
