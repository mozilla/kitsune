import re

from kitsune.search import es_utils
from kitsune.search.models import Synonym


class SynonymParseError(SyntaxError):
    def __init__(self, errors, *args, **kwargs):
        super(SynonymParseError, self).__init__(*args, **kwargs)
        self.errors = errors


def parse_synonyms(text):
    errors = []
    synonyms = set()

    for i, line in enumerate(text.split('\n'), 1):
        line = line.strip()
        if not line:
            continue
        count = line.count('=>')
        if count < 1:
            errors.append('Syntax error on line %d: No => found.' % i)
        elif count > 1:
            errors.append('Syntax error on line %d: Too many => found.' % i)
        else:
            from_words, to_words = [s.strip() for s in line.split('=>')]
            synonyms.add((from_words, to_words))

    if errors:
        raise SynonymParseError(errors)
    else:
        return synonyms


def count_out_of_date():
    es = es_utils.get_es()

    index_name = es_utils.read_index('default')
    settings = (es.indices.get_settings(index_name)
                .get(index_name, {})
                .get('settings', {}))

    synonym_key_re = re.compile(
        r'index\.analysis\.filter\.synonyms-.*\.synonyms\.\d+')

    synonyms_in_es = set()
    for key, val in settings.items():
        print key, val
        if synonym_key_re.match(key):
            print '^' * 15
            synonyms_in_es.add(val)

    synonyms_in_db = set(unicode(s) for s in Synonym.objects.all())

    synonyms_to_add = synonyms_in_db - synonyms_in_es
    synonyms_to_remove = synonyms_in_es - synonyms_in_db

    import q
    q(synonyms_to_remove)
    q(synonyms_to_add)
    if synonyms_to_remove == set(['firefox => firefox']):
        synonyms_to_remove = set()

    return (len(synonyms_to_add), len(synonyms_to_remove))
