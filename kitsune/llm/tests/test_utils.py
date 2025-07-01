from unittest.mock import patch, Mock

from langchain.schema.output_parser import OutputParserException

from kitsune.llm.utils import build_chain_with_retry
from kitsune.sumo.tests import TestCase


@patch("kitsune.llm.utils.coerce_to_runnable", side_effect=lambda x: x)
class BuildChainWithRetryTestCase(TestCase):

    def setUp(self):
        self.prompt = Mock()
        self.llm = Mock()
        self.parser = Mock()
        self.prompt.__or__ = Mock(return_value=self.llm)
        self.llm.__or__ = Mock(return_value=self.parser)

    def test_build_chain_with_retry(self, coerce_mock):
        expected_result = dict(is_something=True, reason="Because")
        self.parser.invoke.side_effect = [OutputParserException("error"), expected_result]
        chain = build_chain_with_retry(self.prompt, self.llm, self.parser)
        self.assertEqual(chain.invoke({}), expected_result)

    def test_build_chain_with_retry_when_max_retries_exceeded(self, coerce_mock):
        self.parser.invoke.side_effect = [
            OutputParserException("first error"),
            OutputParserException("second error"),
        ]
        chain = build_chain_with_retry(self.prompt, self.llm, self.parser)
        self.assertIsNone(chain.invoke({}))

    def test_build_chain_with_retry_when_max_retries_exceeded_and_default(self, coerce_mock):
        self.parser.invoke.side_effect = [
            OutputParserException("first error"),
            OutputParserException("second error"),
        ]
        default_result = dict(default=True)
        chain = build_chain_with_retry(
            self.prompt, self.llm, self.parser, default_result=default_result
        )
        self.assertEqual(chain.invoke({}), default_result)

    def test_build_chain_with_retry_when_max_retries_adjusted(self, coerce_mock):
        expected_result = dict(is_something=True, reason="Because")
        self.parser.invoke.side_effect = [
            OutputParserException("first error"),
            OutputParserException("second error"),
            expected_result,
        ]
        chain = build_chain_with_retry(self.prompt, self.llm, self.parser, max_retries=2)
        self.assertEqual(chain.invoke({}), expected_result)
