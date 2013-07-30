;
define('ace/mode/sumo', function(require, exports, module) {

var oop = require('ace/lib/oop');
var TextMode = require('ace/mode/text').Mode;
var Tokenizer = require('ace/tokenizer').Tokenizer;
var SUMOHighlightRules = require('ace/mode/sumo_highlight_rules').SUMOHighlightRules;
var SUMOBehaviour = require('ace/mode/behaviour/sumo').SUMOBehaviour;

var Mode = function() {
    this.$tokenizer = new Tokenizer(new SUMOHighlightRules().getRules());
    this.$behaviour = new SUMOBehaviour();
};
oop.inherits(Mode, TextMode);
exports.Mode = Mode;
});

define('ace/mode/sumo_highlight_rules', function(require, exports, module) {

var oop = require('ace/lib/oop');
var TextHighlightRules = require('ace/mode/text_highlight_rules').TextHighlightRules;

var SUMOHighlightRules = function() {
        // see: https://developer.mozilla.org/en/JavaScript/Reference/Global_Objects
    var identifierRe = '[a-zA-Z0-9\\$_\u00a1-\uffff][a-zA-Z\\d\\$_\u00a1-\uffff]*\\b';

    this.$rules = {
        'start' : [
        {
            token: 'variable.language',
            regex: '__TOC__'
        },
        {
            token: ['variable.language', 'meta.tag.name'],
            regex: /(\{)(for)/,
            next: 'fx_version_os_version'
        },
        {
            token: ['variable.language', 'meta.tag.name'],
            regex: /(\{)(note|warning)/,
            next: 'close_tag'
        },
        {
            token: 'variable.language',
            regex: /\{\/(for|note|warning)\}/,
        },
        {
            token: 'meta.tag',
            regex: /<\/?br>/
        },
        {
            token: ['variable.language', 'meta.tag', 'markup.italic', 'variable.language'],
            regex: /(\{)(filepath|key|menu|button|pref)(.*?)(\})/
        },
        {
            token: ['markup.other.link', 'markup.other.link', 'markup.other.link', 'markup.other.link'],
            regex: /(\[{2})([^\]]*?)(\|.*?)(\]{2})/
        },
        {
            token: ['markup.other.link', 'markup.other.link', 'markup.other.link', 'markup.other.link'],
            regex: /(\[{2})(\S*:)(.*?)(\]{2})/
        },
        {
            token: ['markup.other.link', 'markup.other.link', 'markup.other.link'],
            regex: /(\[{2})(.*?)(\]{2})/
        },
        {
            token: ['markup.other.link', 'markup.other.link', 'markup.other.link', 'markup.other.link'],
            regex: /(\[)(\S*)(.*?)(\])/
        },
        {
            token: ['variable.language', 'markup.bold', 'variable.language'],
            regex: /(''')(.*?)(''')/
        },
        {
            token: ['variable.language', 'markup.italic', 'variable.language'],
            regex: /('')(.*?)('')/
        },
        {
            token: ['variable.language', 'markup.underline', 'variable.language'],
            regex: /(<u>)(.*?)(<\/u>)/
        },
        {
            token: ['variable.language', 'markup.strikethrough', 'variable.language'],
            regex: /(<s>)(.*?)(<\/s>)/
        },
        {
            token: ['variable.language', 'markup.strikethrough', 'variable.language'],
            regex: /(<del>)(.*?)(<\/del>)/
        },
        {
            token: ['variable.language', 'comment'],
            regex: /(<nowiki>)(.*?)/,
            next: 'nowiki'
        },
        {
            token: ['variable.language', 'comment'],
            regex: /(<code>)(.*?)/,
            next: 'code'
        },
        {
            token: ['variable.language', 'comment'],
            regex: /(<pre>)(.*?)/,
            next: 'pre'
        },
        {
            token: 'markup.quote',
            regex: /^\s+.*/
        },
        {
            token: ['markup.bold', 'markup.bold', 'markup.bold'],
            regex: /^(={1,6})(.*?)(\1)$/
        },
        {
            token: 'variable.language',
            regex: /^[\-]{4}/
        },
        {
            token: 'variable.language',
            regex: /^[;:#\*]+/
        },
        {
            token: 'variable.language',
            regex: /^\{?[\|!][+\-]?\}?/
        },
        {
            token : 'comment',
            merge : true,
            regex : '<\\!--',
            next : 'comment'
        },
        {
            token: "identifier",
            regex: identifierRe
        }],
        comment: [{
            token : 'comment',
            regex : '.*?-->',
            next : 'start'
        }, {
            token : 'comment',
            merge : true,
            regex : '.+'
        }],
        nowiki: [{
            token: ['variable.language'],
            regex: /(<\/nowiki>)/,
            next: 'start'
        }],
        code: [{
            token: ['variable.language'],
            regex: /(<\/code>)/,
            next: 'start'
        },
        {
            token: ['variable.language'],
            regex: /(<\/?nowiki>)/
        }],
        pre: [{
            token: ['variable.language'],
            regex: /(<\/pre>)/,
            next: 'start'
        },
        {
            token: ['variable.language'],
            regex: /(<\/?nowiki>)/
        }],
        space: [
            {token : "text", regex : "\\s+"}
        ],
        close_tag: [{
            token: 'variable.language',
            regex: /\}/,
            next: 'start'
        }],
        fx_version_os_version: [{
            token: 'markup.italic',
            regex: /((,\s?)?(not\s)?((win(xp|7|8)?|mac|linux|android|maemo)|=?(fx|tb|m)\d*))+/,
            next: 'close_tag'
        },
        {
            token: 'variable.language',
            regex: /\{\/for\}/,
        }]
    };
};

oop.inherits(SUMOHighlightRules, TextHighlightRules);

exports.SUMOHighlightRules = SUMOHighlightRules;
});

define('ace/mode/behaviour/sumo', ['require', 'exports', 'module' , 'ace/lib/oop', 'ace/mode/behaviour', 'ace/token_iterator'], function(require, exports, module) {

var oop = require('../../lib/oop');
var Behaviour = require('../behaviour').Behaviour;
var TokenIterator = require('../../token_iterator').TokenIterator;

function hasType(token, type) {
    var _hasType = true;
    var typeList = token.type.split('.');
    var needleList = type.split('.');
    needleList.forEach(function(needle){
        if (typeList.indexOf(needle) == -1) {
            _hasType = false;
            return false;
        }
    });
    return _hasType;
}

var SUMOBehaviour = function () {
    this.add("autoclosing", "insertion", function (state, action, editor, session, text) {
        var voidElements = ['key', 'menu', 'button', 'pref'];
        if (text == '}') {
            var position = editor.getCursorPosition();
            var iterator = new TokenIterator(session, position.row, position.column);
            var token = iterator.getCurrentToken();
            if (token && hasType(token, 'string') && iterator.getCurrentTokenColumn() + token.value.length > position.column)
                return;
            var atCursor = false;
            if (!token || !hasType(token, 'meta.tag') && !(hasType(token, 'text') && token.value.match('/'))) {
                do {
                    token = iterator.stepBackward();
                } while (token && (hasType(token, 'string') || hasType(token, 'keyword.operator') || hasType(token, 'entity.attribute-name') || hasType(token, 'text')));
            } else {
                atCursor = true;
            }
            if (!token || !hasType(token, 'meta.tag.name') || iterator.stepBackward().value.match('/')) {
                return;
            }
            var element = token.value;
            if (atCursor) {
                var element = element.substring(0, position.column - token.start);
            }
            if (voidElements.indexOf(element) !== -1) {
                return;
            }
            return {
               text: '}' + '{/' + element + '}',
               selection: [1, 1]
            };
        }
    });
};
oop.inherits(SUMOBehaviour, Behaviour);

exports.SUMOBehaviour = SUMOBehaviour;
});

define('ace/snippets/sumo', ['require', 'exports', 'module' ], function(require, exports, module) {

// The formatting of this needs to stay intact, or snippets won't work
exports.snippetText = "# Basic formatting\n\
snippet bold\n\
\t'''${1:text}'''\n\
snippet italics\n\
\t''${1:text}''\n\
snippet underline\n\
\t<u>${1:text}</u>\n\
snippet superscript\n\
\t<sup>${1:text}</sup>\n\
snippet subscript\n\
\t<sub>${1:text}</sub>\n\
snippet strikethrough\n\
\t<del>${1:text}</del>\n\
snippet code\n\
\t<code>${1:code}</code>\n\
snippet horizontalRule\n\
\t----\n\
snippet linkArticle\n\
\t[[${1:title}]]\n\
snippet linkArticleCustomTitle\n\
\t[[${1:title}|${2:text}]]\n\
snippet linkExternal\n\
\t[${1:url}]\n\
snippet linkExternalCustomTitle\n\
\t[${1:url} ${2:text}]\n\
snippet listNumbered\n\
\t# ${1:itemOne}\n\
\t# ${2:itemTwo}\n\
\t# ${3:itemThree}\n\
snippet listUnordered\n\
\t* ${1:itemOne}\n\
\t* ${2:itemTwo}\n\
\t* ${3:itemThree}\n\
snippet table\n\
\t{|\n\
\t|+ ${1:table caption}\n\
\t!${2:column_name}!!${3:column_name}\n\
\t|-\n\
\t|${4:row1col1}||${5:row1col2}\n\
\t|-\n\
\t|${6:row2col1}||${7:row2cols2}\n\
\t|}\n\
snippet toc\n\
\t__TOC__\n\
snippet comment\n\
\t<!-- ${1:text} -->\n\
snippet heading6\n\
\t====== ${1:text} ======\n\
snippet heading5\n\
\t===== ${1:text} =====\n\
snippet heading4\n\
\t==== ${1:text} ====\n\
snippet heading3\n\
\t=== ${1:text} ===\n\
snippet heading2\n\
\t== ${1:text} ==\n\
snippet heading1\n\
\t= ${1:text} =\n\
snippet for\n\
\t{for ${1:os_or_firefox_version}}${2:text}{/for}\n\
snippet note\n\
\t{note}${1:note text}{/note}\n\
snippet warning\n\
\t{warning}${1:warning text}{/warning}\n\
snippet preference\n\
\t{pref ${1:pref value}}\n\
snippet filepath\n\
\t{filepath ${1:path}}\n\
snippet key\n\
\t{key ${1:key or shortcut}}\n\
snippet menu\n\
\t{menu ${1:label}}\n\
snippet button\n\
\t{button ${1:label}}\n\
snippet definitionlist\n\
\t; ${1:Term}\n\
\t: ${2:Definition}\n\
\t; ${3:Term}\n\
\t: ${4:Definition a}\n\
\t: ${5:Definition b}\n\
\t:: ${6:Reference}\n\
snippet image\n\
\t[[Image:${1:image title}]]\n\
snippet video\n\
\t[[Video:${1:video title}]]\n\
";
exports.scope = "sumo";

});
