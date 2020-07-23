from collections import namedtuple
import json
import os

Language = namedtuple("Language", "english native iso639_1")

file = os.path.join(os.path.dirname(__file__), "languages.json")
with open(file, "r") as f:
    locales = json.loads(f.read())

LOCALES = {}

for k in locales:
    LOCALES[k] = Language(locales[k]["english"], locales[k]["native"], locales[k]["iso639_1"])
