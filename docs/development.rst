===========
Development
===========

This covers loosely how we do big feature changes.


Changes that involve database migrations
========================================

Any changes to the database (model fields, model field data, adding
permissions, ...) need a migration.

We use `schematic <https://github.com/jbalogh/schematic>`_ for
migrations.


Running migrations
------------------

To run migrations, you do::

    ./vendor/src/schematic/schematic migrations/

It'll perform any migrations that haven't been performed, yet.


Creating a new migration
------------------------

Each migration increases the schema version number by 1. You can
figure out which schema your database is running by doing::

    ./vendor/src/schematic/schematic -v migrations

Migrations are stored in files in ``migrations/``.

To create a new migration, you'll create a new file in the
``migrations/`` directory. The first part of the filename is the
schema version number. Then a dash. Then some name that indicates what
the migration is for. See the directory for examples.

There are a bunch of ways to create the substance of the file. It
depends on what it is you're trying to do. One way is to base it on
the output of::

    ./manage.py sqlall <appname>

for the app that you made changes to, then editing that down to the
bits needed.

.. Note::

   If you have CREATE TABLE statements, make sure they end with setting
   the engine to InnoDB. For example::

       CREATE TABLE `topics_topic` (
           `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
           `title` varchar(255) NOT NULL,
           `slug` varchar(50) NOT NULL,
           `description` longtext NOT NULL,
           `image` varchar(250),
           `parent_id` integer,
           `display_order` integer NOT NULL,
           `visible` bool NOT NULL
       ) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;


.. Note::

   If you created new models, make sure to insert the content type and
   default permissions. e.g. Something like this::

      INSERT INTO django_content_type (name, app_label, model) VALUES
          ('record', 'search', 'record');
      SET @ct = (SELECT id from django_content_type WHERE app_label='search'
          and model='record');
      INSERT INTO auth_permission (name, content_type_id, codename) VALUES
          ('Can add record', @ct, 'add_record'),
          ('Can change record', @ct, 'change_record'),
          ('Can delete record', @ct, 'delete_record'),
          ('Can run a full reindexing', @ct, 'reindex');


Testing a migration
-------------------

You can dump your db to a file to save its state, then run the
migrations. That way if the migration has bugs, you can restore your
database.


Changes that involve reindexing
===============================

With Elastic Search, it takes a while to reindex. We need to be able
to reindex without taking down search.

This walks through the workflow for making changes to our Elastic
Search code that require reindexing.


Things about non-trivial changes
--------------------------------

1. We should roll multiple reindex-requiring changes into megapacks
   when it makes sense and doesn't add complexity.
2. Developers should test changes with recent sumo dumps.


Workflow for making the changes
-------------------------------

1. work on the changes in a separate branch (just like everything else
   we do)
2. make a pull request
3. get the pull request reviewed
4. rebase the changes so they're in two commits:

   1. a stage 1 commit that changes ``ES_WRITE_INDEXES``, updates the
      mappings and updates the indexing code
   2. a stage 2 commit that changes ``ES_INDEXES``, changes
      ``ES_WRITE_INDEXES``, and changes the search view code

   **Avoid cosmetic changes that don't need to be made (e.g. pep-8
   fixes, etc.)**

5. push those changes to the same pull request
6. get those two changes reviewed

Once that's ok, then that branch should get updated from master, then
pushed to stage to get tested.

That branch should **not** land in master, yet.


Workflow for reviewing changes
------------------------------

Go through and do a normal review.

After everything looks good, the developer should rebase the changes
so they're in a stage 1 commit and a stage 2 commit.

At that point:

1. Verify each commit individually. Make sure the code is
   correct. Make sure the tests pass. Make sure the site is
   functional.
2. Verify that the ``ES_INDEXES`` and ``ES_WRITE_INDEXES`` settings
   have the correct values in each commit.


Workflow for pushing changes to stage
-------------------------------------

Don't land the changes in master, yet!

If you hit problems, deploy the master branch back to the stage server
and go back to coding/fixing.

1. Push the branch you have your changes in to the official
   mozilla/kitsune remote.
2. Deploy the stage 1 commit to stage.
3. Verify that search still works.
4. Verify that the index settings are correct---look at the
   ``ES_INDEXES`` and ``ES_WRITE_INDEXES`` values.
5. Destructively reindex.
6. Deploy the stage 2 commit to stage.
7. Verify that search still works.
8. Verify that the index settings are correct---look at the
   ``ES_INDEXES`` and ``ES_WRITE_INDEXES`` values.
9. Verify bugs that were fixed with the new search code.


Workflow for pushing those changes to production
------------------------------------------------

If we're also doing a production push, first push next to production and
verify that everything is fine. Then continue.

1. Tell the other sumo devs to hold off on pushing to master branch
   and deploying. Preferably by email and IRC.
2. Once you've told everyone, land the changes in master.
3. Deploy the stage 1 commit to production.
4. Verify that search works.
5. Destructively reindex to the new write index.
6. When reindexing is done, push the stage 2 commit to production.
7. Verify that search works.
8. Verify bugs that were fixed with the new search code.

Pretty sure this process allows us to back out at any time with
minimal downtime.


On the next day
---------------

If everything is still fine, then merge the special branch into master
and delete the old read index.

Announce "STUCK THE LANDING!" after a successful mapping change
deployment.
