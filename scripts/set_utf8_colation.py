import os

from django.db import connection

DEFAULT_COLATION = "utf8_unicode_ci"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kitsune.settings")


def run(colation=DEFAULT_COLATION):

    db_tables = connection.introspection.table_names()

    with connection.cursor() as cursor:
        for table in db_tables:
            print(f"Setting colation for table {table}")
            cursor.execute(
                f"ALTER TABLE {table} CONVERT TO CHARACTER SET utf8 COLLATE {colation};"
            )


if __name__ == "__main__":
    print('Run with "./manage.py runscript set_utf8_colation')
