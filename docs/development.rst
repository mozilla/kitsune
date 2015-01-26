===========
Development
===========

This covers loosely how we do big feature changes.

Changes that involve new dependencies
=====================================

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

    python scripts/peep.py install -r requirements/default.txt --no-use-wheel

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

We use `South <http://south.readthedocs.org/en/latest/index.html>`_
for migrations.


Running migrations
------------------

To run migrations, you do::

    $ ./manage.py migrate

It'll perform any migrations that haven't been performed for all apps.


Setting up an app for migrations
--------------------------------

New apps need to have the migration structure initialized. To do that,
do::

    $ ./manage.py schemamigration <appname> --initial


Creating a new migration
------------------------

There are two kinds of migrations: schema migrations and data
migrations.

To create a new schema migration, do::

    $ ./manage.py schemamigration <appname> --auto


South can figure out a lot of it for you. You can see the list of
things it'll probably get right `in the South autodetector docs
<http://south.readthedocs.org/en/latest/autodetector.html#autodetector-supported-actions>`_.

For everything else, you can run the auto and then tweak the migration.

To create a new data migration, do::

    $ ./manage.py datamigration <appname>


For obvious reasons, there is no "auto" mode for data migrations.


More about migrations
---------------------

Definitely read the chapter of the South tutorial on `teams and
workflow
<http://south.readthedocs.org/en/latest/tutorial/part5.html>`_.
That'll answer a lot of questions about how to write and test
migrations.

For many of your questions, `the South tutorial
<http://south.readthedocs.org/en/latest/tutorial/index.html>`_
contains the answers.

For other questions, definitely check out the `South documentation
<http://south.readthedocs.org/en/latest/index.html>`_.

For questions that aren't answered there, ask someone and/or try
Googling the answer.


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
