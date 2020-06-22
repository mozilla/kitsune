import os

path = os.path.join(os.path.dirname(__file__), 'tlds-alpha-by-domain.txt')

with open(path) as f:
    VALID_TLDS = set(f.read().splitlines()[1:])
