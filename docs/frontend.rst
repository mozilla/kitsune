=======================
Frontend Infrastructure
=======================

.. warning::
    This section of documentation may be outdated.

Frontends assets for Kitsune are managed through `Django Pipeline`_.

.. _Django Pipeline: https://django-pipeline.readthedocs.io/


Bundles
=======

To reduce the number of requests per page and increase overall performance,
JS and CSS resources are grouped into *bundles*. These are defined in
``kitsune/bundles.py``, and are loaded into pages with template tags. Each
bundle provides a list of files which will be compiled (if necessary), minified,
and concatenated into the final bundle product.

In development, the minification and concatenation steps are skipped. In
production, each file is renamed to contain a hash of it's contents in the
name, and files are rewritten to account for the changed names. This is
called cache busting, and allows the CDN to be more aggressive in caching these
resources, and for clients to get updates faster when we make changes.

Style Sheets
============

The styles written for Kitsune is mostly written in `Sass`_ using the SCSS synatax.

Sass files are recognized by an extension of ``.scss``.

.. _Sass: https://sass-lang.com/

Javascript
==========

There are a few kinds of Javascript in use in Kitsune.

Plain JS
--------

Plain JS is not suspect to any compilation step, and is only minified and
concatenated. Plain JS files should be written to conform to ES5 standards, for
compatibility.

Plain JS files have an extension of ``.js``.

ES6 and beyond
--------------

Files with an extension of ``.es6`` are compiled by `Babel`_ to ES5.

.. _Babel: https://babeljs.io/
