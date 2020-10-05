import logging
import time

from django.conf import settings
from django.utils.module_loading import import_string


log = logging.getLogger("k.lib.email")


class LoggingEmailBackend(object):
    """
    Wraps a email backend defined in Django's settings and logs everything it does.
    """

    def __init__(self, *args, **kwargs):
        self._batch_id = None
        # Set up the real backend
        RealBackend = import_string(settings.EMAIL_LOGGING_REAL_BACKEND)
        self.real_backend = RealBackend(*args, **kwargs)

    @property
    def batch_id(self):
        """Get a batch_id, or lazily make a new one."""
        if self._batch_id is None:
            # This is the number of milliseconds since the last midnight. It
            # doesn't need to be globally unique, just unique enough to
            # distinguish between email tasks that happen at a similar time.
            self._batch_id = int(time.time() * 1000) % (1000 * 60 * 60 * 24)
        return self._batch_id

    def log(self, level, msg):
        """Write a log message, prepending the current batch id."""
        log.log(level, "Batch %s - %s" % (self.batch_id, msg))

    def open(self):
        """Open a network connection."""
        new_conn = self.real_backend.open()

        # Checking for True or False directly instead of relying on trutheyness
        # to avoid catching non-booleans
        if new_conn is True:
            self.log(logging.DEBUG, "Succesfully opened new connection.")
        elif new_conn is False:
            self.log(logging.DEBUG, "Did not open a new connection. (Either cached or failed)")
        elif new_conn is None:
            self.log(logging.DEBUG, "Opened a new connection. (Unknown status)")
        else:
            # If new_conn is not True, False, or None, the backend is
            # not behaving as expected. Blow up.
            raise AssertionError(
                "Unexpected return from email backend open method: %r." % (new_conn,)
            )

        return new_conn

    def close(self):
        """Close a network connection."""
        ret = self.real_backend.close()
        self.log(logging.DEBUG, "Closed connection.")
        # Clear the batch ID, in case this backend object is re-used.
        self._batch_id = None
        return ret

    def send_messages(self, messages):
        """
        Sends one or more EmailMessage objects and returns the number of email messages sent.
        """
        num_to_send = len(messages)

        # Build a big, multiline log "line" that lists all the emails we are trying to send.
        first_line = "Attempting to send %(count)s emails: " % {"count": num_to_send}
        msg_lines = [
            "%(subject)s - %(recipients)r"
            % {
                "subject": message.subject,
                "recipients": ", ".join(str(r) for r in message.recipients()),
            }
            for message in messages
        ]
        self.log(logging.DEBUG, first_line + "\n\t".join(msg_lines))

        # Some backend sometimes return None when they don't attempt to send messsages.
        num_sent = self.real_backend.send_messages(messages) or 0

        if num_sent == num_to_send:
            # Success
            self.log(logging.DEBUG, "Succesfully sent %(sent)s emails." % {"sent": num_sent})
        elif num_sent < num_to_send:
            self.log(
                logging.ERROR,
                "Failed to send all emails. Sent %(sent)s out of %(to_send)s."
                % {
                    "sent": num_sent,
                    "to_send": num_to_send,
                },
            )
        else:
            # Somehow the backend sent more emails than we asked for.
            # Something is very wrong here.
            raise AssertionError("Sent more emails than requested.")

        return num_sent
