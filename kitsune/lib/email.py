import smtplib

from django.core.mail.backends import smtp
from sentry_sdk import capture_exception


class SMTPEmailBackendWithSentryCapture(smtp.EmailBackend):
    """
    A wrapper around Django's smtp.EmailBackend that captures OSError and
    smtplib.SMTPException exceptions in Sentry, but otherwise behaves as
    if failures were silently ignored.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fail_silently = False

    def open(self):
        try:
            return super().open()
        except OSError as err:
            capture_exception(err)
            return None

    def close(self):
        try:
            return super().close()
        except smtplib.SMTPException as err:
            capture_exception(err)
            return None

    def _send(self, email_message):
        try:
            return super()._send(email_message)
        except smtplib.SMTPException as err:
            capture_exception(err)
            return False
