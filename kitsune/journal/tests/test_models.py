from kitsune.journal.models import RECORD_ERROR, RECORD_INFO, Record
from kitsune.sumo.tests import TestCase


class RecordManagerTests(TestCase):
    def test_info_records_at_info_level(self):
        Record.objects.info("test.src", "nothing to see")

        record = Record.objects.get()
        self.assertEqual(RECORD_INFO, record.level)

    def test_error_records_at_error_level(self):
        Record.objects.error("test.src", "something broke")

        record = Record.objects.get()
        self.assertEqual(RECORD_ERROR, record.level)

    def test_message_is_stored_as_plain_text(self):
        Record.objects.info("test.src", "user {username} did {what}", username="ringo", what="it")

        self.assertEqual("user ringo did it", Record.objects.get().msg)
