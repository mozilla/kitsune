import difflib


class BetterHtmlDiff(difflib.HtmlDiff):
    """Modified version of HtmlDiff.

    * Replaces nowrap="nowrap" hard-coded style with a class
    * Only replaces every other consecutive space with a &nbsp; to allow for
      line wrapping.

    For producing HTML side by side comparison with change highlights.

    This class can be used to create an HTML table (or a complete HTML file
    containing the table) showing a side by side, line by line comparison
    of text with inter-line and intra-line change highlights.  The table can
    be generated in either full or contextual difference mode.

    The following methods are provided for HTML generation:

    make_table -- generates HTML for a single side by side table
    make_file -- generates complete HTML file with a single side by side table

    See tools/scripts/diff.py for an example usage of this class.
    """
    def _format_line(self, side, flag, linenum, text):
        """Returns HTML markup of "from" / "to" text lines

        side -- 0 or 1 indicating "from" or "to" text
        flag -- indicates if difference on line
        linenum -- line number (used for line number column)
        text -- line text to be marked up
        """
        try:
            linenum = '%d' % linenum
            id = ' id="%s%s"' % (self._prefix[side], linenum)
        except TypeError:
            # handle blank lines where linenum is '>' or ''
            id = ''
        # replace those things that would get confused with HTML symbols
        text = text.replace('&', '&amp;').replace('>', '&gt;')
        text = text.replace('<', '&lt;')

        text = text.replace('  ', '&nbsp; ').rstrip()

        return '<td class="diff_header"%s>%s</td><td class="text">%s</td>' \
               % (id, linenum, text)
