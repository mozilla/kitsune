=========
Questions
=========

This document explains what kinds of question states exist in Kitsune,
how they are set and their implications.

Question States
===============

Not yet posted
--------------
Questions are created within the `Ask a question` workflow,
but they are not shown in question listings until the user is confirmed.
With Persona for authentication this status is impossible,
since email addresses are confirmed right away.


Default
-------
This is the unmarked state of the thread.

Implications:
1. Users can reply
2. Visible in regular SUMO searches (with at least one helpful reply)
3. Visible to external searches
4. Visible in the regular questions list
5. Visible in the `related threads` section


Locked
------
This is the locked state of a thread. A thread can be locked in two ways:
1. By manually locking it via the question UI
2. Automatically after 180 days.

Implications:
1. Users can't reply
2. Moderators can unlock to reply
3. If there is an answer, the locked thread is still shown by search
engines and our internal search.
4. If there is no answer, the locked thread will not be shown by search
engines and our internal search.


Not indexed
-----------
Questions with no answers that are older than 30 days have a meta tag telling
 search engines not to show them.
