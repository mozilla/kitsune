/*
 * Wrapper around diff_match_patch. or something like that.
 */

(function($) {

'use strict';

function Diff(from, to, outputContainer) {
    /* Args:
     * from, to - the text to create a diff of
     * outputContainer - container element for the diff html output
     */
    Diff.prototype.init.call(this, from, to, outputContainer);
}

Diff.prototype = {
    init: function(from, to, outputContainer) {
        var self = this;

        self.from = from;
        self.to = to;
        self.$container = $(outputContainer);
        self.$container.html('<div class="diff-html" />');
        self.$diff = self.$container.find('.diff-html');

        self.rawDiffs = self._diff();
        self.lineDiffs = self._lineDiff();

        self.render();
    },
    _diff: function() {
        // Do the initial diff with diff_match_patch.
        var self = this;
        var dmp = new diff_match_patch();
        dmp.Match_Threshold = 0.5;
        dmp.Match_Distance = 1000;
        var d = dmp.diff_main(self.from, self.to);
        dmp.diff_cleanupSemantic(d);
        return d;
    },
    _lineDiff: function() {
        // Convert the diff_match_patch diff to a line-by-line diff.
        var self = this;
        var ampRegex = /&/g;
        var ltRegex = /</g;
        var gtRegex = />/g;
        var paraRegex = /\n/g;
        var fromLineNum = 1;
        var toLineNum = 1;
        var lines = [];
        var fromContinued = false;
        var toContinued = false;
        var line, fromLine, toLine, sectionLines, i, l, op, data, text;

        _.each(self.rawDiffs, function(diff) {
            op = diff[0];    // Operation (insert, delete, equal)
            data = diff[1];  // Text of change.
            text = data
                .replace(ampRegex, '&amp;')
                .replace(ltRegex, '&lt;')
                .replace(gtRegex, '&gt;')
                .replace(' ', '&nbsp;');

            sectionLines = text.split(paraRegex);

            for (i = 0, l = sectionLines.length; i < l; i++) {
                if (!fromContinued && !toContinued) {
                    fromLine = toLine = {
                        changes: false,
                        hasFrom: false,
                        hasTo: false,
                        parts: []
                    };
                    lines.push(fromLine);
                } else if (!fromContinued) {
                    fromLine = {
                        changes: false,
                        hasFrom: false,
                        hasTo: false,
                        parts: []
                    };
                    lines.push(fromLine);
                    if (!toLine.hasTo) {
                        toLine = fromLine;
                    }
                } else if (!toContinued) {
                    toLine = {
                        changes: false,
                        hasFrom: false,
                        hasTo: false,
                        parts: []
                    };
                    lines.push(toLine);
                    if (!fromLine.hasFrom) {
                        fromLine = toLine;
                    }
                }

                text = sectionLines[i];

                if (op === DIFF_EQUAL) {
                    fromLine.hasFrom = toLine.hasTo = true;
                    if (fromLine === toLine) {
                        fromLine.parts.push([op, sectionLines[i]]);
                    } else {
                        // If we aren't on the same line, change the op to not equal
                        // to avoid weirdness in the outputted diff where it tries to
                        // match across different lines.
                        toLine.parts.push([DIFF_INSERT, sectionLines[i]]);
                        fromLine.parts.push([DIFF_DELETE, sectionLines[i]]);
                    }
                    if (i === l - 1) {
                        if (text.length !== 0) {
                            // The last piece of text didn't have a \n.
                            toContinued = fromContinued = true;
                        } else {
                            toContinued = fromContinued = false;
                        }
                    } else {
                        toContinued = fromContinued = false;
                        if (fromLine.hasFrom) {
                            fromLine.fromLineNum = fromLineNum++;
                        }
                        if (toLine.hasTo) {
                            toLine.toLineNum = toLineNum++;
                        }
                    }
                } else if (op === DIFF_DELETE) {
                    fromLine.hasFrom = true;
                    fromLine.parts.push([op, sectionLines[i]]);
                    if (i === l - 1) {
                        if (text.length !== 0) {
                            // The last piece of text didn't have a \n.
                            fromContinued = true;
                        } else {
                            fromContinued = false;
                        }
                    } else {
                        fromContinued = false;
                        if (fromLine.hasFrom) {
                            fromLine.fromLineNum = fromLineNum++;
                        }
                    }
                    toContinued = true;
                } else if (op === DIFF_INSERT) {
                    toLine.hasTo = true;
                    toLine.parts.push([op, sectionLines[i]]);
                    if (i === l - 1) {
                        if (text.length !== 0) {
                            // The last piece of text didn't have a \n.
                            toContinued = true;
                        } else {
                            toContinued = false;
                        }
                    } else {
                        toContinued = false;
                        if (toLine.hasTo) {
                            toLine.toLineNum = toLineNum++;
                        }
                    }
                    fromContinued = true;
                }
            }
        });
        if (fromLine.hasFrom) {
            fromLine.fromLineNum = fromLineNum++;
        }
        if (toLine.hasTo) {
            toLine.toLineNum = toLineNum++;
        }

        return lines;
    },
    render: function() {
        // Render the diff.
        var self = this;
        self.$diff.html(self.prettyHtml());
    },
    prettyHtml: function() {
        var self = this;
        var html = [];
        var prepend = '';

        html.push('<table><tbody>');

        _.each(self.lineDiffs, function(line) {
            // Check if the line has non-whitespace changes.
            line.changes = _.reduce(line.parts, function(memo, part) {
                return memo || (((part[0] === DIFF_DELETE) || (part[0] === DIFF_INSERT)) && part[1].length > 0);
            }, false);

            // Render the line if it has a line number.
            if (line.fromLineNum || line.toLineNum) {
                self._singleColumnHtml(line, html);
            }
        });

        html.push('</td></tr>');
        html.push('</tbody></table>');

        if (self.from === self.to) {
            prepend = '<p><strong>[' + gettext('No differences found') + ']</strong></p>';
        }
        return prepend + html.join('');
    },
    _singleColumnHtml: function(line, html) {
        // Single column, github style diff.
        var self = this;
        if (!line.changes && line.hasFrom && line.hasTo) {
            self._scEqualRow(line, html);
        } else {
            if (line.hasFrom) {
                self._scFromRow(line, html);
            }
            if (line.hasTo) {
                self._scToRow(line, html);
            }
        }
    },
    _scEqualRow: function(line, html) {
        // Render an equal line.
        var op;

        html.push('<tr class="equal">');
        html.push('<td class="num">', line.fromLineNum, '</td>');
        html.push('<td class="num">', line.toLineNum, '</td>');
        html.push('<td class="mark"></td>');
        html.push('<td>');
        _.each(line.parts, function(part) {
            op = part[0];
            if (op === DIFF_INSERT) {
                html.push('<ins>' + part[1] + '</ins>');
            } else if (op === DIFF_DELETE) {
                html.push('<del>' + part[1] + '</del>');
            } else if (op === DIFF_EQUAL) {
                html.push(part[1]);
            }
        });
        html.push('</td></tr>');
    },
    _scFromRow: function(line, html) {
        // Render a changed from line.
        var op;

        html.push('<tr class="fromLine">');
        html.push('<td class="num">', line.fromLineNum, '</td>');
        html.push('<td class="num"></td>');
        html.push('<td class="mark">-</td>');
        html.push('<td>');
        _.each(line.parts, function(part) {
            op = part[0];
            if (op === DIFF_DELETE) {
                html.push('<del>' + part[1] + '</del>');
            } else if (op === DIFF_EQUAL) {
                html.push(part[1]);
            }
        });
        html.push('</td></tr>');
    },
    _scToRow: function(line, html) {
        // Render a changed to line.
        var op;

        html.push('<tr class="toLine">');
        html.push('<td class="num"></td>');
        html.push('<td class="num">', line.toLineNum, '</td>');
        html.push('<td class="mark">+</td>');
        html.push('<td>');
        _.each(line.parts, function(part) {
            op = part[0];
            if (op === DIFF_INSERT) {
                html.push('<ins>' + part[1] + '</ins>');
            } else if (op === DIFF_EQUAL) {
                html.push(part[1]);
            }
        });
        html.push('</td></tr>');
    }
};

// Apply diffs automatically to '.diff-this' elements using children
// '.from', '.to' and '.output' as the parameters.
function initDiff($container) {
    $container = $container || $('body');
    $container.find('.diff-this').each(function() {
        var $this = $(this);
        var diff = new Diff($this.find('.from').text(), $this.find('.to').text(), $this.find('.output'));
    });
}

window.k = window.k || {};
window.k.Diff = Diff;
window.k.initDiff = initDiff;

initDiff();

})(jQuery);
