from unittest.mock import patch

from django.contrib.auth.hashers import check_password, get_hasher, identify_hasher, make_password
from django.test import SimpleTestCase, override_settings
from django.test.runner import DiscoverRunner

from kitsune.sumo.test_runner import SpawnParallelRunner


class PasswordHashingTests(SimpleTestCase):
    @override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
    def test_runner_restores_password_hashing_after_an_error(self):
        original_algorithm = get_hasher().algorithm
        error = RuntimeError("Test discovery failed")

        def fail_run(*args, **kwargs):
            encoded = make_password("test-password")
            self.assertEqual(identify_hasher(encoded).algorithm, "md5")
            self.assertTrue(check_password("test-password", encoded))
            self.assertFalse(check_password("wrong-password", encoded))
            raise error

        with patch.object(DiscoverRunner, "run_tests", side_effect=fail_run):
            with self.assertRaises(RuntimeError) as raised:
                SpawnParallelRunner(verbosity=0).run_tests([])

        self.assertIs(raised.exception, error)
        self.assertEqual(
            identify_hasher(make_password("test-password")).algorithm, original_algorithm
        )
