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
for getting set up in the :ref:`installation docs <hacking-howto-chapter>`.

If you ever find yourself stuck, come look for us in `#sumodev
<ircs://irc.mozilla.org/sumodev>`_ on Mozilla's IRC network. We're happy to
help!

You'll need a Github account and a Bugzilla account.


The Quick and Dirty
===================

Very quick, very little explanation. Those with strong git fu may already see
some shortcuts. Use them! As long as ``mozilla/master`` doesn't have merge
commits, it's all good.

Assuming your Github account is ``foobar`` and you've already forked Kitsune::

    git clone git@github.com:foobar/kitsune
    cd kitsune
    git remote add mozilla https://github.com/mozilla/kitsune.git
    git fetch mozilla
    git checkout -b temp
    git branch -d master
    git checkout -t mozilla/master
    git branch -d temp

If you haven't set up your local git user, please do before committing any code
for Kitsune. This way you can take credit for your work::

    git config user.email your@github.email
    git config user.name "Your Name"

You should only need to do that once. Here's the bit to do every time::

    git checkout master
    git pull --rebase mozilla master
    git checkout -b my-feature

    # Make a change and commit it.
    $EDITOR path/to/file.py
    git add path/to/file.py
    git commit -m "[Bug 123456] Fooing and the Barring."
    git push origin my-feature

    # Open a pull request, get review.
    # Respond to feedback:
    $EDITOR path/to/file.py
    git add path/to/file.py
    git commit -m "Feedback from Barfoo"

    # r+! Rebase and squash.
    git checkout master
    git pull --rebase mozilla master
    git checkout my-feature
    git rebase -i master  # Squash any feedback commits.

If you don't have commit access::

    git push -f origin my-feature
    # DONE

If you *do* have commit access::

    git checkout master
    git merge my-feature  # Should be a fast-forward commit.
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
    git checkout master
    git checkout -b temp  # Create a temporary local branch.
    git branch -d master  # Delete your local master.
    git checkout -t mozilla/master  # Create a tracking branch.
    git branch -D temp  # Delete your temporary branch.

If you haven't set up your local git user, please do before committing any code
for Kitsune. This way you can take credit for your work::

    git config user.email your@github.email
    git config user.name "Your Name"

The correct way to keep your local master up to date is::

    git checkout master
    git pull --rebase mozilla master

You can avoid typing ``--rebase`` every time by doing::

    git config branch.master.rebase true

More actual code in a minute!


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
yourself in Bugzilla. There's an easy "take" link next to the Assignee field.

You don't need to bother setting the bug to the ``ASSIGNED`` state.


Fix the Bug on a Branch
-----------------------

.. Note::

   This describes the process for fixing a relatively small bug in a
   single-commit. Large features may differ.

All bug fixes, changes, new features, etc, should be done on a "feature
branch", which just means "any branch besides ``master``." You should make sure
your local ``master`` branch is up to date (see above) before starting a new
feature branch.

::

    git checkout master
    git pull --rebase mozilla master  # Update local master.
    git checkout -b my-feature-branch  # Some logical name.

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

    git push origin my-feature-branch

Then, in your browser, navigate to
``https://github.com/<yourname>/kitsune/compare/my-feature-branch`` and hit the
**Pull Request** button. If the commit message is clear, the form should be
filled out enough for you to submit it right away.

We add an ``r?`` in the pull request message indicating that this pull
request is ready to go and is looking for someone to review it.


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


Ready to Merge!
---------------

Once a pull request has gotten an ``r+`` ("R-plus", it's from Bugzilla) it's
ready to merge in. At this point it should be rebased against the current
``mozilla/master`` and any feedback/fixup commits should be squashed.

If you don't have commit access, someone who does may do this for you, if they
have time.

::

    git checkout master
    git pull --rebase mozilla master
    git checkout my-feature-branch
    git rebase -i master  # Update and squash.
    python manage.py test  # Make sure tests still pass.
    git push -f origin my-feature-branch

You're done! Congratulations, soon you'll have code running on one of the
biggest sites in the world!

If you do have commit access, you should land your patch!

Continuing from above::

    git checkout master
    git merge my-feature-branch  # Should say something about "fast-forward".

Before pushing to ``mozilla/master``, I like to verify that the merge went fine
in the logs. For the vast majority of merges, *there should not be a merge
commit*.

::

    git log -5  # Verify that the merge went OK.
    git push mozilla master  # !!! Pushing code to the primary repo/branch!
    # Optionally, you can keep your Github master in sync.
    git push origin master  # Not strictly necessary but kinda nice.
    git push origin :my-feature-branch  # Nice to clean up.

Once the commit is on ``mozilla/master``, you should go to the main repo on
Github and find and copy the URL of the commit. Then go to the bug in Bugzilla,
paste the URL, and set the bug to ``RESOLVED FIXED``. This tells QA and others
that the fix has landed on ``master`` and will be on the dev server soon! And
close the pull request on Github.
