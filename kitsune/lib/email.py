import logging

from django.conf import settings
from django.utils.module_loading import import_string


log = logging.getLogger('k.lib.email')
RealBackend = import_string(settings.EMAIL_LOGGING_REAL_BACKEND)


class LoggingEmailBackend(RealBackend):
    """
    Wraps a email backend defined in Django's settings and logs everything it does.
    """

    def open(self):
        """Open a network connection."""
        new_conn = super(LoggingEmailBackend, self).open()
        # Checking for True or False directly instead of relying on trutheyness
        # to avoid catching non-booleans
        if new_conn is True:
            log.debug('Succesfully opened new connection.')
        elif new_conn is False:
            log.debug('Did not open a new connection. (Either cached or failed)')
        else:
            assert (
                new_conn is None,
                'Unexpected return from email backend open method: %r.' % (new_conn, )
            )
            log.debug('Opened a new connection. (Unknown status)')
        return new_conn

    def close(self):
        """Close a network connection."""
        ret = super(LoggingEmailBackend, self).close()
        log.debug('Closed connection.')
        return ret

    def send_messages(self, email_messages):
        """
        Sends one or more EmailMessage objects and returns the number of email messages sent.
        """
        num_to_send = len(email_messages)

        msg_lines = ['Attempting to send %(count)s emails:' % {'count': num_to_send}]
        for message in email_messages:
            msg_lines.append('\t%(subject)s - %(recipients)r' % {
                'subject': message.subject,
                'recipients': message.recipients(),
            })
        log.debug('\n'.join(msg_lines))

        num_sent = super(LoggingEmailBackend, self).send_messages(email_messages)
        if num_sent is None:
            num_sent = 0
        assert num_sent <= num_to_send, 'Sent more emails than requested'

        if num_sent == num_to_send:
            log.debug('Succesfully sent %(sent)s messages' % {'sent': num_sent})
        else:
            log.error('Failed to send all emails. Sent %(sent)s out of %(to_send)s' % {
                'sent': num_sent,
                'to_send': num_to_send,
            })

        return num_sent
