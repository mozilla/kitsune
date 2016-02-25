.. _patching:

================
Patching Kitsune
================

Submitting a patch to `Kitsune <https://support.mozilla.com>`_ is easy! (Fair
warning: writing the patch may not be ;)

We use `pull requests <https://github.com/mozilla/kitsune/pulls>`_ to manage
patches and code reviews, and `Bugzilla <https://bugzilla.mozilla.org>`_ to
handle actual bug tracking.

Because of our infrastructure and how we do deployments, we've developed a
fairly straight-forward workflow in git for submitting patches. This is
outlined below.

You should run the tests before submitting a pull request. You can find help
for getting set up in the :ref:`installation docs <hacking-howto-chapter>` and
help for running tests in the :ref:`testing docs <tests-chapter>`.

If you ever find yourself stuck, come look for us in `#sumodev
<ircs://irc.mozilla.org/sumodev>`_ on Mozilla's IRC network. We're happy to
help!

You'll need a Github account and a Bugzilla account.


The Quick and Dirty
===================

Very quick, very little explanation. Those with strong git fu may already see
some shortcuts. Use them!

First, clone your fork, and then point the master branch to Mozilla's fork.
Assuming your Github account is ``foobar`` and you've already forked
Kitsune::

    git clone https://github.com/foobar/kitsune
    cd kitsune
    git remote add mozilla https://github.com/mozilla/kitsune.git
    git fetch mozilla
    git checkout -t mozilla/master -B master

If you haven't set up your local git user, please do before committing any code
for Kitsune. This way you can take credit for your work::

    git config user.email your@github.email
    git config user.name "Your Name"

You should only need to do that once. Here's the bit to do every time::

    git checkout master
    git reset --hard mozilla/master
    git checkout -b my-feature-123456

    # Make a change and commit it.
    $EDITOR path/to/file.py
    git add path/to/file.py
    git commit -m "[Bug 123456] Fooing and the Barring."
    git push --set-upstream origin my-feature

    # Open a pull request, get review.
    # Respond to feedback:
    $EDITOR path/to/file.py
    git add path/to/file.py
    git commit -m "Feedback from Barfoo"
    git push

Eventually you'll get an r+. If you have commit access, now you can go ahead
and merge your branch. You may, if you want, rebase your branch to clean up
any embarrassing mistakes, but it isn't required. If you don't have commit
access the next part will be done by someone who does.

There are two options. The first is to press the Big Green Button in GitHub PRs
that says "Merge pull Request". If you would prefer to do it manually (or
if there are merge conflicts, you can do this::

    # r+! Merge
    git checkout master
    git fetch mozilla
    git reset --hard mozilla/master
    git merge --no-ff my-feature-123456
    git push mozilla master  # Bots will alert everyone!
    git push origin master  # Optional but nice.

After the pull request is closed::

    git push origin :my-feature  # Delete the remote branch. Nice to others.
    git branch -D my-feature # Delete the local branch, if you're done.


The Details
===========

This is the process in more detail, for a relatively small change that will
only need one commit, and doesn't need any special treatment, like landing on
special branches.


Fork and Clone Kitsune
----------------------

On Github, hit the **Fork** button. You'll want to clone **your** fork of the
project, at least initially::

    git clone git@github.com:<yourname>/kitsune.git

To help keep up to date, you should add ``mozilla/kitsune`` as a remote::

    cd kitsune
    git remote add mozilla https://github.com/mozilla/kitsune.git

You should avoid changing your ``master`` branch, it should track
``mozilla/master``. This can help::

    git fetch mozilla
    # Update your master branch to track Mozilla's master branch instead.
    git checkout -B master -t mozilla/master # Update your master branch to

If you haven't set up your local git user, please do before committing any code
for Kitsune. This way you can take credit for your work::

    git config user.email your@github.email
    git config user.name "Your Name"

The correct way to keep your local master up to date is::

    git checkout master
    git fetch mozilla
    git reset --hard mozilla/master

This will forcibly move your local master branch to whatever is on the Mozilla
master branch, destroying anything you have committed that wasn't pushed.
Remember to always work on a branch that is not master!


Find a Bug
----------

Step one is to make sure there's a bug in Bugzilla. Obvious "bugs" just need a
Bugzilla bug to track the work for all the involved teams. There are `a number
of open bugs <http://bit.ly/LUTjcY>`_ if you want to try your hand at fixing
something!

New features or changes to features need bugs to build a consensus of
developers, support team members, and community members, before we decide to
make the change. If you want to change something like this, be sure to file the
bug and get a consensus first. We'd hate to have you spend time on a patch we
can't take.


Take the Bug
------------

To make sure no one else is working on the bug at the same time, assign it to
yourself in Bugzilla. If you have the proper permissions there's an easy "take"
link next to the Assignee field. Ask in the IRC for details.

You can assign bugs to yourself even if you aren't going to immediately work on
them (though make sure you will get to them sooner rather than later). Once you
are actively working on a bug, set the bug to the ``ASSIGNED`` state.


Fix the Bug on a Branch
-----------------------

.. Note::

   This describes the process for fixing a relatively small bug in a
   single-commit. Large features may differ.

All bug fixes, changes, new features, etc, should be done on a "feature
branch", which just means "any branch besides ``master``." You should make sure
your local ``master`` branch is up to date (see above) before starting a new
feature branch. Your feature branch should include the bug number in the branch
name, if applicable.

::

    git checkout master
    git fetch mozilla
    git reset --hard upstream/master  # Update local master.
    git checkout -b my-feature-branch-123456  # Some logical name.

Now you're on a feature branch, go ahead and make your changes. Assuming you
haven't added any new files, you can do::

    git commit -a -m "[Bug 123456] Fix the foo and the bar."

If you did add new files, you will have to ``git add`` them before committing.

Note that the commit message contains the bug number after the word "Bug".
This helps us and our IRC bots!


Open a Pull Request
-------------------

Once you have the bug fixed locally, you'll need to push the changes up to
Github so you can open a pull request.

::

    git push --set-upstream origin my-feature-branch

Then, in your browser, navigate to
``https://github.com/<yourname>/kitsune/compare/my-feature-branch`` and hit the
**Pull Request** button. If the commit message is clear, the form should be
filled out enough for you to submit it right away.

We add an ``r?`` in the pull request message indicating that this pull
request is ready to go and is looking for someone to review it.

Othertimes you may want to open a pull request early that isn't quite ready to
merge. This is a great way to share the work that you are doing, and get early
feedback. Make it clear that your PR isn't ready by putting ``[WIP]`` in the
title. Also make sure to say when it is ready! The best way to do this is to
remove ``[WIP]`` from the title and make a comment asking for ``r?``.


Respond to Review
-----------------

It's very rare that pull requests will be checked in immediately. Most of the
time they will go through one or more rounds of code review and clean-up.

Code review is usually comments made on the pull request or commits in Github,
asking for specific changes to be made. If the requested change isn't clear, or
you disagree with it, feel free to ask questions inline. Isn't Github's
line-by-line commenting great?

Assuming a few small changes need to be made, make the changes locally on the
feature branch, then put them in a *new commit*. This makes it easier from
reviewers. For example, if Erik reviewed the pull request and asked for some
fixes, you might do this::

    git checkout my-feature-branch
    # Make the changes.
    git commit -a -m "Feedback from Erik."
    git push origin my-feature-branch

Github will automatically add the new commit to the pull request, so we'll see
it. Leaving it in a separate commit at this stage helps the reviewer see what
changes you've made.

There may be more than one round of feedback, especially for complex bugs. The
process is exactly the same after each round: make the changes, add them in yet
another new commit, push the changes.

There are also a few bots that might interact with your PR. In particular, our
continuous integration service will run tests and style checks on your new
code. All PRs must be approved by the CI system before they will be merged,
so watch out. They show up as either a red X or a green check mark in the
PR.


Ready to Merge!
---------------

Once a pull request has gotten an ``r+`` ("R-plus", it's from Bugzilla) it's
ready to merge in. At this point you can rebase and squash any feedback/fixup
commits you want, but this isn't required.

If you don't have commit access, someone who does may do this for you, if they
have time. Alternatively, if you have commit access, you can press GitHub's
"Merge pull request" button, which does a similar process to below. This is the
preferred way to merge PRs when there are no complications.

::

    git checkout master
    git reset --hard mozilla/master
    git merge --no-ff my-feature-branch-123456
    # Make sure tests pass.
    python manage.py test
    git push


You're done! Congratulations, soon you'll have code running on one of the
biggest sites in the world!

Before pushing to ``mozilla/master``, I like to verify that the merge went fine
in the logs. For the vast majority of merges, *there should not be a merge
commit*.

::

    git log --graph --decorate
    git push mozilla master             # !!! Pushing code to the primary repo/branch!

    # Optionally, you can keep your Github master in sync.
    git push origin master              # Not strictly necessary but kinda nice.
    git push origin :my-feature-branch  # Nice to clean up.

This should automatically close the PR, as GitHub will notice the merge commit.

Once the commit is on ``mozilla/master``, copy the commit url to the bug.

Once the commit has been deployed to stage and prod, set the bug to
``RESOLVED FIXED``. This tells everyone that the fix is in production.
