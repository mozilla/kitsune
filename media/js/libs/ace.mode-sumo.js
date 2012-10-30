define('ace/mode/sumo', function(require, exports, module) {

var oop = require("ace/lib/oop");
var TextMode = require("ace/mode/text").Mode;
var Tokenizer = require("ace/tokenizer").Tokenizer;
var SUMOHighlightRules = require("ace/mode/sumo_highlight_rules").SUMOHighlightRules;
var SUMOBehaviour = require("ace/mode/behaviour/sumo").SUMOBehaviour;

var Mode = function() {
    this.$tokenizer = new Tokenizer(new SUMOHighlightRules().getRules());
    this.$behaviour = new SUMOBehaviour();
};
oop.inherits(Mode, TextMode);

(function() {
    // Extra logic goes here. (see below)
}).call(Mode.prototype);

exports.Mode = Mode;
});

define('ace/mode/sumo_highlight_rules', function(require, exports, module) {

var oop = require("ace/lib/oop");
var TextHighlightRules = require("ace/mode/text_highlight_rules").TextHighlightRules;

var SUMOHighlightRules = function() {
        // see: https://developer.mozilla.org/en/JavaScript/Reference/Global_Objects
    var keywordMapper = this.createKeywordMapper({
        "variable.language":
            "__TOC__",
    }, "identifier");
    // TODO: Unicode escape sequences
    var identifierRe = "[a-zA-Z\\$_\u00a1-\uffff][a-zA-Z\\d\\$_\u00a1-\uffff]*\\b";

    this.$rules = {
        "start" : [{
            token : keywordMapper,
            regex : identifierRe
        },
        {
            token: ["meta.tag", null],
            regex: /({\/?(note|warning)})/,
        },
        {
            token: "meta.tag",
            regex: /<\/?br>/
        },
        {
            token: ["variable.language", "meta.tag", "variable.language", "variable.language"],
            regex: /({\/?)(for)(.*?)(})/
        },
        {
            token: ["variable.language", "meta.tag", "identifier", "variable.language"],
            regex: /({)(filepath|key|menu|button|pref)(.*?)(})/
        },
        {
            token: ["markup.other.link", "markup.other.link", "markup.other.link", "markup.other.link"],
            regex: /(\[{2})([^\]]*?)(\|.*?)(\]{2})/
        },
        {
            token: ["markup.other.link", "markup.other.link", "markup.other.link", "markup.other.link"],
            regex: /(\[{2})(\S*:)(.*?)(\]{2})/
        },
        {
            token: ["markup.other.link", "markup.other.link", "markup.other.link"],
            regex: /(\[{2})(.*?)(\]{2})/
        },
        {
            token: ["markup.other.link", "markup.other.link", "markup.other.link", "markup.other.link"],
            regex: /(\[)(\S*)(.*?)(\])/
        },
        {
            token: ["variable.language", "markup.bold", "variable.language"],
            regex: /(''')(.*?)(''')/
        },
        {
            token: ["variable.language", "markup.italic", "variable.language"],
            regex: /('')(.*?)('')/
        },
        {
            token: ["variable.language", "markup.underline", "variable.language"],
            regex: /(<u>)(.*?)(<\/u>)/
        },
        {
            token: ["variable.language", "markup.strikethrough", "variable.language"],
            regex: /(<s>)(.*?)(<\/s>)/
        },
        {
            token: ["variable.language", "markup.strikethrough", "variable.language"],
            regex: /(<del>)(.*?)(<\/del>)/
        },
        {
            token: ["variable.language", "comment"],
            regex: /(<nowiki>)(.*?)/,
            next: "nowiki"
        },
        {
            token: ["variable.language", "comment"],
            regex: /(<code>)(.*?)/,
            next: "code"
        },
        {
            token: ["variable.language", "comment"],
            regex: /(<pre>)(.*?)/,
            next: "pre"
        },
        {
            token: "markup.quote",
            regex: /^\s+.*/
        },
        {
            token: "variable.language",
            regex: /^[\*#]*\*/
        },
        {
            token: "variable.language",
            regex: /^[\*#]*#/
        },
        {
            token: ["markup.bold", "markup.bold", "markup.bold"],
            regex: /^(={1,6})(.*?)(\1)$/
        },
        {
            token: "variable.language",
            regex: /^[-]{4}/
        },
        {
            token: "variable.language",
            regex: /^[;:]/
        },
        {
            token: "variable.language",
            regex: /^{?[\|!][+-]?}?/,
        },
        {
            token : "comment",
            merge : true,
            regex : "<\\!--",
            next : "comment"
        }
        ],
        comment: [{
            token : "comment",
            regex : ".*?-->",
            next : "start"
        }, {
            token : "comment",
            merge : true,
            regex : ".+"
        }],
        nowiki: [{
            token: ["variable.language"],
            regex: /(<\/nowiki>)/,
            next: "start"
        }],
        code: [{
            token: ["variable.language"],
            regex: /(<\/code>)/,
            next: "start"
        },
        {
            token: ["variable.language"],
            regex: /(<\/?nowiki>)/
        }],
        pre: [{
            token: ["variable.language"],
            regex: /(<\/pre>)/,
            next: "start"
        },
        {
            token: ["variable.language"],
            regex: /(<\/?nowiki>)/
        }]
    };
};

oop.inherits(SUMOHighlightRules, TextHighlightRules);

exports.SUMOHighlightRules = SUMOHighlightRules;
});

define('ace/mode/behaviour/sumo', ['require', 'exports', 'module' , 'ace/lib/oop', 'ace/mode/behaviour', 'ace/token_iterator'], function(require, exports, module) {

var oop = require("../../lib/oop");
var Behaviour = require("../behaviour").Behaviour;
var TokenIterator = require("../../token_iterator").TokenIterator;

function hasType(token, type) {
    var hasType = true;
    var typeList = token.type.split('.');
    var needleList = type.split('.');
    needleList.forEach(function(needle){
        if (typeList.indexOf(needle) == -1) {
            hasType = false;
            return false;
        }
    });
    return hasType;
}

var SUMOBehaviour = function () {
    this.add("autoclosing", "insertion", function (state, action, editor, session, text) {
        if (text == '}') {
            var position = editor.getCursorPosition();
            var iterator = new TokenIterator(session, position.row, position.column);
            var token = iterator.getCurrentToken();
            var closeable = ["for", "note", "warning"];
            var notCloseable = ["key", "menu", "button", "pref"];
            var tag = token.value;
            while(closeable.indexOf(tag) == -1) {
                if(notCloseable.indexOf(tag) != -1 ||
                   tag == "{") {
                    return;
                }
                tag = iterator.stepBackward().value;
            }

            return {
               text: '}' + '{/' + tag + '}',
               selection: [1, 1]
            }
        }
        if (text == "=")
            return {
                text: text + "=",
                selection: [1, 1]
            }

        if (text == "[")
            return {
                text: text + "]",
                selection: [1,1]
            }

        if(text == "(")
            return {
                text: text + ")",
                selection: [1,1]
            }
    });
}
oop.inherits(SUMOBehaviour, Behaviour);

exports.SUMOBehaviour = SUMOBehaviour;
});
