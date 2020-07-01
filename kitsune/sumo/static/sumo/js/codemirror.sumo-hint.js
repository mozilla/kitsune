/* global CodeMirror, jQuery */

(function ($) {
  "use strict";

  CodeMirror.registerHelper("hint", "sumo", function (editor, options) {
    options = $.extend({}, { word: /[\w$-]+/, range: 500 }, options);

    var word = options.word;
    var range = options.range;
    var cur = editor.getCursor();
    var curLine = editor.getLine(cur.line);
    var end = cur.ch;
    var start = end;

    while (start && word.test(curLine.charAt(start - 1))) {
      --start;
    }

    var curWord = start !== end && curLine.slice(start, end);
    var list = [];
    var seen = {};
    var re = new RegExp(word.source, "g");

    for (var dir = -1; dir <= 1; dir += 2) {
      var line = cur.line;
      var endLine =
        Math.min(
          Math.max(line + dir * range, editor.firstLine()),
          editor.lastLine()
        ) + dir;

      for (; line !== endLine; line += dir) {
        var text = editor.getLine(line);
        var m = re.exec(text);

        while (m) {
          if (line === cur.line && m[0] === curWord) {
            continue;
          }
          if (
            (!curWord || m[0].lastIndexOf(curWord, 0) === 0) &&
            !Object.prototype.hasOwnProperty.call(seen, m[0])
          ) {
            seen[m[0]] = true;
            list.push(m[0]);
          }
          m = re.exec(text);
        }
      }
    }
    return {
      list: list,
      from: new CodeMirror.Pos(cur.line, start),
      to: new CodeMirror.Pos(cur.line, end),
    };
  });
})(jQuery);
