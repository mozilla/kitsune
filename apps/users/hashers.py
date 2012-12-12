import hashlib

from django.contrib.auth.hashers import BasePasswordHasher, mask_hash
from django.utils.crypto import constant_time_compare
from django.utils.datastructures import SortedDict

from tower import ugettext as _


class SHA256PasswordHasher(BasePasswordHasher):
    """The SHA256 password hashing algorithm."""
    algorithm = "sha256"

    def encode(self, password, salt):
        assert password
        assert salt and '$' not in salt
        hash = hashlib.sha256(salt + password).hexdigest()
        return "%s$%s$%s" % (self.algorithm, salt, hash)

    def verify(self, password, encoded):
        algorithm, salt, hash = encoded.split('$', 2)
        assert algorithm == self.algorithm
        encoded_2 = self.encode(password, salt)
        return constant_time_compare(encoded, encoded_2)

    def safe_summary(self, encoded):
        algorithm, salt, hash = encoded.split('$', 2)
        assert algorithm == self.algorithm
        return SortedDict([
            (_('algorithm'), algorithm),
            (_('salt'), mask_hash(salt, show=2)),
            (_('hash'), mask_hash(hash)),
        ])

class PasswordDisabledHasher(BasePasswordHasher):
    """The SHA256 password hashing algorithm.

    We "expire" user passwords by setting them to "PASSWORD_DISABLED".
    This fake hasher handles them without blowing up.
    """
    algorithm = "PASSWORD_DISABLED"

    def encode(self, password, salt):
        return self.algorithm

    def verify(self, password, encoded):
        return False

    def safe_summary(self, encoded):
        return SortedDict([
            (_('algorithm'), self.algorithm),
            (_('salt'), ''),
            (_('hash'), ''),
        ])
