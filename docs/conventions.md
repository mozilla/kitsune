---
title: Conventions
---

This document contains coding conventions, and things to watch out for,
etc.

# Coding conventions

We follow most of the practices as detailed in the [Mozilla webdev
bootcamp
guide](https://mozweb.readthedocs.io/en/latest/guide/development_process.html).

It is recommended that you [install pre-commit](hacking_howto.md/#install-lintingtools)

## Type hints

When creating and/or modifying Python functions/methods, we add [type
hints](https://docs.python.org/3/library/typing.html) to their arguments
and result, but only when it makes sense. See [our Architectural Decision Record](architecture/decisions/0004-type-checking.md) for more details.

# Git conventions

## Git workflow

See [patching](patching.md) for how we use Git, branches and merging.

## Git commit messages

Git commit messages should have the following form:

    [bug xxxxxxx] Short summary

    Longer explanation with paragraphs and lists and all that where
    each line is under 72 characters.

    * bullet 1
    * bullet 2

    Etc. etc.

Summary line should be capitalized, short and should not exceed 50
characters. Why? Because this is a convention many git tools take
advantage of.

If the commit relates to a bug, the bug should show up in the summary
line in brackets.

There should be a blank line between the summary and the rest of the
commit message. Lines should not exceed 72 characters.

See [these guidelines](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html)
for some more explanation.

## Git resources and tools

See [Webdev bootcamp guide](https://mozweb.readthedocs.io/en/latest/reference/git_github.html) for:

-   helpful resources for learning git
-   helpful tools
