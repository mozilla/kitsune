"""
The products' strings: reading them from GitHub once a day, and looking them up.

- `sources.py` lists the repositories and where each owner's files are in them.
- `github.py`, `sync.py` and `parsers/` download a repository and read its files.
- `shipped_locales.py` and `locales.py` say which locales an owner ships, and what
  it calls them.
- `spots.py` groups an owner's strings into spots, and finds the strings with a
  label's text.
- `catalogs.py` reads what an owner's strings say in one locale.
"""
