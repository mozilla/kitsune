"""
Utitilities for working with synonyms, both in the database and in ES.
"""

import re

from kitsune.search import es_utils
from kitsune.search.models import Synonym


class SynonymParseError(Exception):
    """One or more parser errors were found. Has a list of errors found."""

    def __init__(self, errors, *args, **kwargs):
        super(SynonymParseError, self).__init__(*args, **kwargs)
        self.errors = errors


def parse_synonyms(text):
    """
    Parse synonyms from user entered text.

    The input should look something like

        foo => bar
        baz, qux => flob, glork

    :returns: A set of 2-tuples, ``(from_words, to_words)``. ``from_words``
        and ``to_words`` will be strings.
    :throws: A SynonymParseError, if any errors are found.
    """

    errors = []
    synonyms = set()

    for i, line in enumerate(text.split("\n"), 1):
        line = line.strip()
        if not line:
            continue
        count = line.count("=>")
        if count < 1:
            errors.append("Syntax error on line %d: No => found." % i)
        elif count > 1:
            errors.append("Syntax error on line %d: Too many => found." % i)
        else:
            from_words, to_words = [s.strip() for s in line.split("=>")]
            synonyms.add((from_words, to_words))

    if errors:
        raise SynonymParseError(errors)
    else:
        return synonyms


def count_out_of_date():
    """
    Count number of synonyms that differ between the database and ES.

    :returns: A 2-tuple where the first element is the number of synonyms
        that are in the DB but not in ES, and the second element is the
        number of synonyms in ES that are not in the DB.
    """
    es = es_utils.get_es()

    index_name = es_utils.write_index("default")
    settings = (
        es.indices.get_settings(index_name).get(index_name, {}).get("settings", {})
    )

    synonym_key_re = re.compile(r"index\.analysis\.filter\.synonyms-.*\.synonyms\.\d+")

    synonyms_in_es = set()
    for key, val in settings.items():
        if synonym_key_re.match(key):
            synonyms_in_es.add(val)

    synonyms_in_db = set(unicode(s) for s in Synonym.objects.all())

    synonyms_to_add = synonyms_in_db - synonyms_in_es
    synonyms_to_remove = synonyms_in_es - synonyms_in_db

    if synonyms_to_remove == set(["firefox => firefox"]):
        synonyms_to_remove = set()

    return (len(synonyms_to_add), len(synonyms_to_remove))
