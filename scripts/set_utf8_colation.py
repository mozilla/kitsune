import os

from django.db import connection

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kitsune.settings")


def run(*args):

    db_name = "kitsune"
    if args:
        db_name = args[0]

    with connection.cursor() as cursor:
        cursor.execute(f"ALTER DATABASE {db_name} CHARACTER SET utf8 COLLATE utf8_general_ci;")


if __name__ == "__main__":
    print('Run with "./manage.py runscript set_utf8_colation')
