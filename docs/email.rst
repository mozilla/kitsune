.. _email-chapter:

==================
Email from Kitsune
==================

The default settings for Kitsune *do not send email*. However, outgoing email
is printed to the the command line.

Viewing email through Mailcatcher
=================================

To view the contents of outgoing email in a slightly easier form than the command line, `Mailcatcher <https://mailcatcher.me/>`_ can be used. This still won't send the email, but show a web-based "outbox" with the contents of all email which would be sent if Kitsune was hooked up to an email server.

The docker-compose config includes a mailcatcher container, which can be brought up with::

    docker-compose up mailcatcher

Kitsune should then be configured to use it::

    EMAIL_LOGGING_REAL_BACKEND = django.core.mail.backends.smtp.EmailBackend
    EMAIL_HOST = mailcatcher
    EMAIL_HOST_USER =
    EMAIL_HOST_PASSWORD =
    EMAIL_PORT = 1025
    EMAIL_USE_TLS = False

Now all outgoing email will be captured, and can be viewed through http://localhost:1080/.
