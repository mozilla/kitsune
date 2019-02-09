=======================
Frontend Infrastructure
=======================

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

The styles written for Kitsune is written in `Less`_. Libraries, of course,
have styles written in CSS. These are combined into bundles and shipped as
minified CSS.

Less files are recognized by an extension of ``.less``.

.. _Less: http://lesscss.org/

Javascript
==========

There are a few kinds of Javascript in use in Kitsune.

Plain JS
--------

Plain JS is not suspect to any compilation step, and is only minified and
concatenated. Plain JS files should be written to conform to ES3 standards, for
compatibility.

Plain JS files have an extension of ``.js``.

ES6 JavaScript
--------------

EcmaScript 6 is the next version JavaScript that has been recently
standardized. Because it is very new, it does not have wide spread browser
support yet, and so it is compiled using `Babel`_ to ES5. Because it is
compiled to ES5, and not ES3, it is not suitable for use in user facing parts
of the site, which require maximum compatibility.

These files are recognized by the ES6 compiler by an extension of ``.es6``, and
*should* end in ``.js.es6`` for clarity. However, see the note about Browserify
below.

For more information about ES6 syntax and features, see
`lukehoban/es6features`_.

.. _Babel: https://babeljs.io/
.. _lukehoban/es6features: https://github.com/lukehoban/es6features

JSX
---

JSX is a syntax extension on top of ES6 (and in some places, ES7) which adds
support for an XML-like trees. It is used in Kitsune as a way to specify DOM
elements in React Component render methods. JSX is compiled using Babel as
well, and in fact all ES6 files may contain JSX syntax, since Babel compiles
it by default.

These files don't have a specific individual extension, but use the ``.es6``
extension. For clarity, standalone jsx files should use the extension of
``.jsx.es6``.

Browserify
----------

Files with the extension ``.browserify.js`` are treated as Browserify entry
points. They may include other JS files using `ES6 modules syntax`_. The files
included in this way may also make use of the ES6 module system, regardless of
their extension.

All files loaded this way are treated as ES6+JSX files. This is generally the
only way ES6 and JSX code should be included in a bundle, and so in practice
the extensions assigned to those files don't matter to Django Pipeline, and
should be named to be clear to the reader.

Browserify has been configured with the babelify and bowerify transformers, to
be able to load ES6 files and files from Bower.

.. _ES6 modules syntax: https://github.com/lukehoban/es6features#modules


Bower
=====

Frontend dependencies are downloaded using Bower. In a bundle file, they are
listed as ``package-name/path/in/package.js``. Django Pipeline will find the
correct Bower package to pull files from.

Bower is not normally compatible with Browserify. A Browserify transformer
called bowerify makes an include request for Bower packages load the primary
entry point of the Bower package to make them compatible.
