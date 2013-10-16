.. _quickstart:

Quick start guide
=================

Installing polib
----------------

polib requires python 2.5 or superior.

There are several ways to install polib, this is explained 
in :ref:`the installation section <installation>`.

For the impatient, the easiest method is to install polib via
`pip <http://pip.openplans.org/>`_, just type:: 

    pip install polib


Some basics about gettext catalogs
----------------------------------

A gettext catalog is made up of many entries, each entry holding the relation
between an original untranslated string and its corresponding translation. 

All entries in a given catalog usually pertain to a single project, and all
translations are expressed in a single target language. One PO file entry has
the following schematic structure::

    #  translator-comments
    #. extracted-comments
    #: reference...
    #, flag...
    msgid untranslated-string
    msgstr translated-string

A simple entry can look like this::

    #: lib/error.c:116
    msgid "Unknown system error"
    msgstr "Error desconegut del sistema"

polib has two main entry points for working with gettext catalogs:

* the :func:`~polib.pofile` and :func:`~polib.mofile` functions to **load**
  existing po or mo files,
* the :class:`~polib.POFile` and :class:`~polib.MOFile` classes to **create**
  new po or mo files.

References
* `Gettext Manual <http://www.gnu.org/software/gettext/manual/>`_
* `PO file format <http://www.gnu.org/software/gettext/manual/html_node/gettext_9.html>`_
* `MO file format <http://www.gnu.org/software/gettext/manual/html_node/gettext_136.html>`_


Loading existing catalogs
-------------------------

Loading a catalog and detecting its encoding
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here the encoding of the po file is auto-detected by polib (polib detects it by
parsing the charset in the header of the pofile)::

    import polib
    po = polib.pofile('path/to/catalog.po')


Loading a catalog and specifying explicitly the encoding
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For some reason you may want to specify the file encoding explicitely (because
the charset is not specified in the po file header for example), to do so::

    import polib
    po = polib.pofile(
        'path/to/catalog.po',
        encoding='iso-8859-15'
    )

Loading an mo file
~~~~~~~~~~~~~~~~~~

In some cases you can be forced to load an mo file (because the po file is not
available for example), polib handles this case::

    import polib
    mo = polib.mofile('path/to/catalog.mo')
    print mo

As for po files, mofile also allows to specify the encoding explicitely.


Creating po catalogs from scratch
---------------------------------

polib allows you to create catalog from scratch, this can be done with the
POFile class, for exemple to create a simple catalog you could do::

    import polib

    po = polib.POFile()
    po.metadata = {
        'Project-Id-Version': '1.0',
        'Report-Msgid-Bugs-To': 'you@example.com',
        'POT-Creation-Date': '2007-10-18 14:00+0100',
        'PO-Revision-Date': '2007-10-18 14:00+0100',
        'Last-Translator': 'you <you@example.com>',
        'Language-Team': 'English <yourteam@example.com>',
        'MIME-Version': '1.0',
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Transfer-Encoding': '8bit',
    }

This snippet creates an empty pofile, with its metadata, and now you can add
you entries to the po file like this::

    entry = polib.POEntry(
        msgid=u'Welcome',
        msgstr=u'Bienvenue',
        occurrences=[('welcome.py', '12'), ('anotherfile.py', '34')]
    )
    po.append(entry)

To save your file to the disk you would just do::

    po.save('/path/to/newfile.po')

And to compile the corresponding mo file::

    po.save_as_mofile('/path/to/newfile.mo')


More examples
-------------

Iterating over entries
~~~~~~~~~~~~~~~~~~~~~~

Iterating over **all** entries (by default POFiles contains all catalog
entries, even obsolete and fuzzy entries)::

    import polib

    po = polib.pofile('path/to/catalog.po')
    for entry in po:
        print entry.msgid, entry.msgstr

Iterating over **all** entries except obsolete entries::

    import polib

    po = polib.pofile('path/to/catalog.po')
    valid_entries = [e for e in po if not e.obsolete]
    for entry in valid_entries:
        print entry.msgid, entry.msgstr

Iterating over translated entries only::

    import polib

    po = polib.pofile('path/to/catalog.po')
    for entry in po.translated_entries():
        print entry.msgid, entry.msgstr

And so on... 
You could also iterate over the list of POEntry objects returned by the 
following POFile methods:

* :meth:`~polib.POFile.untranslated_entries`
* :meth:`~polib.POFile.fuzzy_entries`


Getting the percent of translated entries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    import polib

    po = polib.pofile('path/to/catalog.po')
    print po.percent_translated()


Compiling po to mo files and reversing mo files to po files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compiling a po file::

    import polib

    po = polib.pofile('path/to/catalog.po')
    # to get the binary representation in a variable:
    modata = po.to_binary()
    # or to save the po file as an mo file
    po.save_as_mofile('path/to/catalog.mo')


Reverse a mo file to a po file::

    mo = polib.mofile('path/to/catalog.mo')
    # to get the unicode representation in a variable, just do:
    podata = unicode(mo)
    # or to save the mo file as an po file
    mo.save_as_pofile('path/to/catalog.po')

