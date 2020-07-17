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

Actually sending email
======================

If you want to get email, you should
double check one thing first: are there any rows in the
``notifications_eventwatch`` table? If there are, you may be sending email to
**real users**. The script in ``scripts/anonymize.sql`` will truncate this
table. Simply run it against your Kitsune database::

    mysql -u kitsune -p <YOUR_PASSWORD> < scripts/anonymize.sql

So now you know you aren't emailing real users, but you'd still like to email
yourself and test email in general. There are a few settings you'll need to
use.

First, set the ``EMAIL_BACKEND``. This document assumes you're using the SMTP
mail backend.

::

    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


If you have ``sendmail`` installed and working, that should do it. However, you
might get caught in spam filters. An easy workaround for spam filters or not
having sendmail working is to send email via a Gmail account.

::

    EMAIL_USE_TLS = True
    EMAIL_PORT = 587
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_HOST_USER = '<your gmail address>@gmail.com'
    EMAIL_HOST_PASSWORD = '<your gmail password>'


Yeah, you need to put your Gmail password in a plain text file on your
computer. It's not for everyone. Be **very** careful copying and pasting
settings from ``.env`` if you go this route.
