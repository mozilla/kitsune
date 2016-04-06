===========
Development
===========

This covers loosely how we do big feature changes.

Changes that involve new Python dependencies
============================================

We use peep to install dependencies. That means that all dependencies have an
associated hash (or several) that are checked at download time. This ensures
malicious code doesn't sneak in through dependencies being hacked, and also
makes sure we always get the exact code we developed against. Changes in
dependencies, malicious or not, will set of red flags and require human
intervention.

A peep requirement stanza looks something like this::

    # sha256: mmQhHJajJiuyVFrMgq9djz2gF1KZ98fpAeTtRVvpZfs
    Django==1.6.7

hash lines can be repeated, and other comments can be added. The stanza is
delimited by non-comment lines (such as blank lines or other requirements).

To add a new dependency, you need to get a hash of the dependency you are
installing. There are several ways you could go about this. If you already have
a tarball (or other appropriate installable artifact) you could use ``peep hash
foo.tar.gz``, which will give the base64 encoded sha256 sum of the artifact,
which you can then put into a peep stanza.

If you don't already have an artifact, you can simply add a line to the
requirements file without a hash, for example ``Django``. Without a version,
peep will grab the latest version of the dependency. If that's not what you
want, put a version there too, like ``Django==1.6.7``.

Now run peep with::

    ./peep.sh install -r requirements/default.txt

Peep will download the appropriate artifacts (probably a tarball), hash it, and
print out something like::

    The following packages had no hashes specified in the requirements file, which
    leaves them open to tampering. Vet these packages to your satisfaction, then
    add these "sha256" lines like so:


    # sha256: mmQhHJajJiuyVFrMgq9djz2gF1KZ98fpAeTtRVvpZfs
    Django==1.6.7

Copy and paste that stanza into the requirements file, replacing the hash-less
stanza you had before. Now re-run peep to install the file for real. Look
around and make sure nothing horrible went wrong, and that you got the right
package. When you are satisfied that you have what you want, commit, push, and
rejoice.


Changes that involve database migrations
========================================

Any changes to the database (model fields, model field data, adding
permissions, ...) require a migration.


Running migrations
------------------

To run migrations, you do::

    $ ./manage.py migrate

It'll perform any migrations that haven't been performed for all apps.


Creating a schema migration
---------------------------

To create a new migration the automatic way:

1. make your model changes
2. run::

       ./manage.py makemigrations <app>


   where ``<app>`` is the app name (sumo, wiki, questions, ...).

3. add a module-level docstring to the new migration file specifying
   what it's doing since we can't easily infer that from the code
   because the code shows the new state and not the differences
   between the old state and the new stage

4. run the migration on your machine::

       ./manage.py migrate

5. run the tests to make sure everything works
6. add the new migration files to git
7. commit


.. seealso::

   https://docs.djangoproject.com/en/1.7/topics/migrations/#adding-migrations-to-apps
     Django documentation: Adding migrations to apps


Creating a data migration
=========================

Creating data migrations is pretty straight-forward in most cases.

To create a data migration the automatic way:

1. run::

       ./manage.py makemigrations --empty <app>

   where ``<app>`` is the app name (sumo, wiki, questions, ...).

2. edit the data migration you just created to do what you need it to
   do
3. make sure to add `reverse_code` arguments to all `RunPython` operations
   which undoes the changes
4. add a module-level docstring explaining what this migration is doing
5. run the migration forwards and backwards to make sure it works
   correctly
6. add the new migration file to git
7. commit

.. seealso::

   https://docs.djangoproject.com/en/1.7/topics/migrations/#data-migrations
     Django documentation: Data Migrations

.. seealso::

   https://docs.djangoproject.com/en/1.7/ref/migration-operations/#runpython


Data migrations for data in non-kitsune apps
--------------------------------------------

If you're doing a data migration that adds data to an app that's not
part of kitsune, but is instead a library (e.g. django-waffle), then
create the data migration in the sumo app and add a dependency to
the latest migration in the library app.

For example, this adds a dependency to django-waffle's initial migration::

    class Migration(migrations.Migration):

        dependencies = [
            ...
            ('waffle', '0001_initial'),
            ...
        ]



.. _changes_reindexing:

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
