import os

# downloaded from https://data.iana.org/TLD/tlds-alpha-by-domain.txt
path = os.path.join(os.path.dirname(__file__), "tlds-alpha-by-domain.txt")

with open(path) as f:
    VALID_TLDS = set(f.read().splitlines()[1:])
