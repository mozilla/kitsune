import logging

from django.test import SimpleTestCase

from kitsune.retrieval.events import UnsafeEventField, emit


class EmitTests(SimpleTestCase):
    def test_the_event_name_is_the_message_and_fields_ride_on_the_record(self):
        with self.assertLogs("k.retrieval", level="INFO") as logs:
            emit("retrieval.sync.completed", locale="en-US", chunk_count=3)

        [record] = logs.records
        self.assertEqual(record.getMessage(), "retrieval.sync.completed")
        self.assertEqual(record.locale, "en-US")
        self.assertEqual(record.chunk_count, 3)

    def test_the_level_can_be_raised(self):
        with self.assertLogs("k.retrieval", level="WARNING") as logs:
            emit("retrieval.sync.skipped", level=logging.WARNING, reason="no_target")
        self.assertEqual(logs.records[0].levelno, logging.WARNING)

    def test_a_bounded_mapping_of_short_values_is_allowed(self):
        with self.assertLogs("k.retrieval", level="INFO") as logs:
            emit("retrieval.sync.completed", outcomes={"index_a": "no_op"})
        self.assertEqual(logs.records[0].outcomes, {"index_a": "no_op"})


class PrivacyTests(SimpleTestCase):
    """Reject obvious sensitive fields and payload-shaped values."""

    def test_fields_named_after_sensitive_payloads_are_refused(self):
        for name in (
            "text",
            "content",
            "content_text",
            "html",
            "key",
            "summary",
            "keywords",
            "vector",
            "content_vector",
            "token",
            "credentials",
            "access_group_ids",
            "group_ids",
            "restrict_to_groups",
        ):
            with self.subTest(field=name), self.assertRaises(UnsafeEventField):
                emit("retrieval.sync.completed", **{name: "anything"})
        with self.assertRaises(UnsafeEventField):
            emit("retrieval.sync.completed", payload={"text": "nested"})

    def test_a_sequence_value_is_refused_so_a_vector_cannot_be_logged(self):
        # A vector is a list of floats; rejecting sequences outright removes the whole class,
        # regardless of what the field is called.
        for value in ([0.1, 0.2], (0.1, 0.2), {0.1, 0.2}):
            with self.subTest(value=type(value).__name__), self.assertRaises(UnsafeEventField):
                emit("retrieval.sync.completed", payload=value)

    def test_an_arbitrary_object_is_refused(self):
        with self.assertRaises(UnsafeEventField):
            emit("retrieval.sync.completed", payload=object())

    def test_a_long_string_is_truncated_rather_than_refused(self):
        with self.assertLogs("k.retrieval", level="INFO") as logs:
            emit("retrieval.sync.completed", slug="x" * 5_000)

        logged = logs.records[0].slug
        self.assertLess(len(logged), 5_000)
        self.assertTrue(logged.endswith("…"))

    def test_names_reserved_by_logging_are_refused(self):
        # These would raise inside logging itself, at the call site of whoever emitted.
        for name in ("message", "module", "args", "levelname"):
            with self.subTest(field=name), self.assertRaises(UnsafeEventField):
                emit("retrieval.sync.completed", **{name: "clash"})
