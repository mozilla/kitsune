from nose.tools import eq_

from testfixtures import LogCapture

from django.test.utils import override_settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMessage

from kitsune.lib.email import LoggingEmailBackend
from kitsune.sumo.tests import TestCase


class MockEmailBackend(BaseEmailBackend):
    """A mock email backend."""

    def __init__(self, *args, **kwargs):
        super(MockEmailBackend, self).__init__(*args, **kwargs)
        self._is_open = False
        self._sent_messages = False

    def open(self):
        self._is_open = True

    def close(self):
        self._is_open = False

    def send_messages(self, messages):
        self._sent_messages = True


class SucceedingMockEmailBackend(MockEmailBackend):
    """
    A mock email backend that pretends to always succeed.

    It mimics the return values of django.core.mail.backends.SMTPEmailBackend
    for the open method.
    """

    def open(self):
        # The SMTP backend returns True if a new connection was opened.
        super(SucceedingMockEmailBackend, self).open()
        return True

    def send_messages(self, messages):
        """
        Sends one or more EmailMessage objects and returns the number of email
        messages sent.
        """
        super(SucceedingMockEmailBackend, self).send_messages(messages)
        return len(messages)


class FailingMockEmailBackend(MockEmailBackend):
    """
    A mock email backend that pretends to always fail.

    It mimics the return values of django.core.mail.backends.SMTPEmailBackend
    for the open method.
    """

    def open(self):
        # The SMTP backend returns False if no new connection was opened.
        # This isn't always failure, sometimes it means a cached connection
        # is used.
        super(FailingMockEmailBackend, self).open()
        return False

    def send_messages(self, messages):
        super(FailingMockEmailBackend, self).send_messages(messages)
        return 0


class FlakyMockEmailBackend(MockEmailBackend):
    """
    A mock email backend that pretends to send exactly half-rounded-down of the
    emails it is asked to send per batch.

    It does not mimic the SMTP backend.
    """

    def send_messages(self, messages):
        super(FlakyMockEmailBackend, self).send_messages(messages)
        return len(messages) / 2


@override_settings(EMAIL_BACKEND="kitsune.lib.email.LoggingEmailBackend")
class TestLoggingEmailBackend(TestCase):
    """
    Test that the logging email backend works as expected.
    """

    def setUp(self):
        self.expected_logs = []
        self.log_capture = LogCapture()

    def expect_log(self, message, logger="k.lib.email", level="DEBUG", check=True):
        self.expected_logs.append((logger, level, message))
        if check:
            self.log_capture.check(*self.expected_logs)

    @override_settings(
        EMAIL_LOGGING_REAL_BACKEND="django.core.mail.backends.base.BaseEmailBackend"
    )
    def test_fail_silently(self):
        # Make sure fail_silently is passed through to the real backend.
        logging_backend = LoggingEmailBackend(fail_silently=True)
        eq_(logging_backend.real_backend.fail_silently, True)

    # The below tests validate several things in 3 cases. The 3 cases are:
    #
    # * The email backend always suceeds.
    # * The email backend always fails.
    # * The email backend sometimes fails and sometimes suceeds.
    #
    # The things that are validated are:
    #
    # * The requested backend is used.
    # * The correct messages are logged.
    # * When a method on the logging backend is called, the corresponding
    #   method is called on the real backend.
    #
    # The three test cases are both very large, and very similar. They
    # could likely be split up into smaller tests, and/or de-duplicated to
    # factor out the similar bits of code. This is left as an exercise for
    # the reader.

    @override_settings(
        EMAIL_LOGGING_REAL_BACKEND="kitsune.lib.tests.test_email.SucceedingMockEmailBackend"
    )
    def test_success_logging(self):
        # setup and make sure we have the right mock backend
        logging_backend = LoggingEmailBackend()
        batch_id = logging_backend.batch_id
        eq_(logging_backend.real_backend.__class__, SucceedingMockEmailBackend)
        eq_(logging_backend.real_backend._is_open, False)
        eq_(logging_backend.real_backend._sent_messages, False)

        # Open a connection
        eq_(logging_backend.open(), True)
        self.expect_log("Batch %i - Succesfully opened new connection." % (batch_id,))
        eq_(logging_backend.real_backend._is_open, True)

        # Send 3 messages
        messages = [
            EmailMessage(subject="subject%i" % i, to=["%i@example.com" % i])
            for i in range(3)
        ]
        eq_(logging_backend.send_messages(messages), 3)
        log_msg = (
            "Batch %i - Attempting to send 3 emails: subject0 - '0@example.com'\n"
            "\tsubject1 - '1@example.com'\n"
            "\tsubject2 - '2@example.com'" % (batch_id,)
        )
        self.expect_log(log_msg, check=False)
        self.expect_log("Batch %i - Succesfully sent 3 emails." % (batch_id,))
        eq_(logging_backend.real_backend._sent_messages, True)

        # Close
        eq_(logging_backend.close(), None)
        self.expect_log("Batch %i - Closed connection." % (batch_id,))
        eq_(logging_backend.real_backend._is_open, False)

    @override_settings(
        EMAIL_LOGGING_REAL_BACKEND="kitsune.lib.tests.test_email.FailingMockEmailBackend"
    )
    def test_failing_logging(self):
        # Setup and make sure we have the right mock backend
        logging_backend = LoggingEmailBackend()
        batch_id = logging_backend.batch_id
        eq_(logging_backend.real_backend.__class__, FailingMockEmailBackend)
        eq_(logging_backend.real_backend._is_open, False)
        eq_(logging_backend.real_backend._sent_messages, False)

        # Open a connection
        eq_(logging_backend.open(), False)
        self.expect_log(
            "Batch %i - Did not open a new connection. (Either cached or failed)"
            % (batch_id,)
        )
        eq_(logging_backend.real_backend._is_open, True)

        # Send 3 messages
        messages = [
            EmailMessage(subject="subject%i" % i, to=["%i@example.com" % i])
            for i in range(3)
        ]
        eq_(logging_backend.send_messages(messages), 0)
        log_msg = (
            "Batch %i - Attempting to send 3 emails: subject0 - '0@example.com'\n"
            "\tsubject1 - '1@example.com'\n"
            "\tsubject2 - '2@example.com'" % (batch_id,)
        )
        self.expect_log(log_msg, check=False)
        self.expect_log(
            "Batch %i - Failed to send all emails. Sent 0 out of 3." % (batch_id,),
            level="ERROR",
        )
        eq_(logging_backend.real_backend._sent_messages, True)

        # Close
        eq_(logging_backend.close(), None)
        self.expect_log("Batch %i - Closed connection." % (batch_id,))
        eq_(logging_backend.real_backend._is_open, False)

    @override_settings(
        EMAIL_LOGGING_REAL_BACKEND="kitsune.lib.tests.test_email.FlakyMockEmailBackend"
    )
    def test_flaky_logging(self):
        # Setup and make sure we have the right mock backend
        logging_backend = LoggingEmailBackend()
        batch_id = logging_backend.batch_id
        eq_(logging_backend.real_backend.__class__, FlakyMockEmailBackend)
        eq_(logging_backend.real_backend._is_open, False)
        eq_(logging_backend.real_backend._sent_messages, False)

        # Open a connection
        eq_(logging_backend.open(), None)
        self.expect_log(
            "Batch %i - Opened a new connection. (Unknown status)" % (batch_id,)
        )
        eq_(logging_backend.real_backend._is_open, True)

        # Send 3 messages
        messages = [
            EmailMessage(subject="subject%i" % i, to=["%i@example.com" % i])
            for i in range(3)
        ]
        eq_(logging_backend.send_messages(messages), 1)
        log_msg = (
            "Batch %i - Attempting to send 3 emails: subject0 - '0@example.com'\n"
            "\tsubject1 - '1@example.com'\n"
            "\tsubject2 - '2@example.com'" % (batch_id,)
        )
        self.expect_log(log_msg, check=False)
        self.expect_log(
            "Batch %i - Failed to send all emails. Sent 1 out of 3." % (batch_id,),
            level="ERROR",
        )
        eq_(logging_backend.real_backend._sent_messages, True)

        # Close
        eq_(logging_backend.close(), None)
        self.expect_log("Batch %i - Closed connection." % (batch_id,))
        eq_(logging_backend.real_backend._is_open, False)
