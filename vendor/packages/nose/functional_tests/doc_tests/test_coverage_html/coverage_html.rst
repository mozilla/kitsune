Generating HTML Coverage with nose
----------------------------------

.. Note ::

    HTML coverage requires Ned Batchelder's `coverage.py`_ module.
..

Console coverage output is useful but terse. For a more browseable view of
code coverage, the coverage plugin supports basic HTML coverage output.

.. hide this from the actual documentation:
    >>> from nose.plugins.plugintest import run_buffered as run
    >>> import os
    >>> support = os.path.join(os.path.dirname(__file__), 'support')
    >>> cover_html_dir = os.path.join(support, 'cover')
    >>> cover_file = os.path.join(os.getcwd(), '.coverage')
    >>> if os.path.exists(cover_file):
    ...     os.unlink(cover_file)
    ...


The console coverage output is printed, as normal.

    >>> from nose.plugins.cover import Coverage
    >>> cover_html_dir = os.path.join(support, 'cover')
    >>> run(argv=[__file__, '-v', '--with-coverage', '--cover-package=blah', 
    ...           '--cover-html', '--cover-html-dir=' + cover_html_dir,
    ...           support, ], 
    ...     plugins=[Coverage()]) # doctest: +REPORT_NDIFF
    test_covered.test_blah ... hi
    ok
    <BLANKLINE>
    Name    Stmts   Miss  Cover   Missing
    -------------------------------------
    blah        4      1    75%   6
    ----------------------------------------------------------------------
    Ran 1 test in ...s
    <BLANKLINE>
    OK

The html coverage reports are saved to disk in the directory specified by the
``--cover-html-dir`` option. In that directory you'll find ``index.html``
which links to a detailed coverage report for each module in the report. The
detail pages show the module source, colorized to indicated which lines are
covered and which are not. There is an example of this HTML output in the
`coverage.py`_ docs.

.. hide this from the actual documentation:
    >>> os.path.exists(cover_file)
    True
    >>> os.path.exists(os.path.join(cover_html_dir, 'index.html'))
    True
    >>> os.path.exists(os.path.join(cover_html_dir, 'blah.html'))
    True

.. _`coverage.py`: http://nedbatchelder.com/code/coverage/
