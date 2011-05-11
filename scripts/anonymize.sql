-- Does a quick anonymization of a SUMO database. Note that this does
-- not necessarily clear out all confidential information and should
-- not be considered approval to distribute this SUMO database.
-- Talk to jsocol if you have questions.

UPDATE auth_user SET
    email = CONCAT('user',id,'@example.com'),
    password = 'sha256$f538347e82$5098e89186fd307d4bb6fe29ac476e72cf96175617fa933a9bd6b3d89a8b0946'; -- 'testpass'

TRUNCATE tidings_watchfilter;

TRUNCATE tidings_watch;

TRUNCATE django_session;

TRUNCATE messages_inboxmessage;

TRUNCATE messages_outboxmessage_to;

TRUNCATE messages_outboxmessage;

UPDATE django_site SET
    domain = 'support-local.allizom.org',
    name = 'support-local.allizom.org';
