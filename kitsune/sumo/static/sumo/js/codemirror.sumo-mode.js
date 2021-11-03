import CodeMirror from "codemirror";

(function() {
  'use strict';

  CodeMirror.defineSimpleMode('sumo', {
    start: [
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
        regex: /\{\/(for|note|warning)\}/
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
        token: 'variable.language',
        regex: /<nowiki>/,
        next: 'nowiki'
      },
      {
        token: 'variable.language',
        regex: /<code>/,
        next: 'code'
      },
      {
        token: 'variable.language',
        regex: /<pre>/,
        next: 'pre'
      },
      {
        token: 'markup.quote',
        regex: /^\s+.*/,
        sol: true
      },
      {
        token: ['markup.bold', 'markup.bold', 'markup.bold'],
        regex: /^(={1,6})(.*?)(\1)$/,
        sol: true
      },
      {
        token: 'variable.language',
        regex: /^[\-]{4}/,
        sol: true
      },
      {
        token: 'variable.language',
        regex: /^[;:#\*]+/,
        sol: true
      },
      {
        token: 'variable.language',
        regex: /^\{?[\|!][+\-]?\}?/,
        sol: true
      },
      {
        token: 'comment',
        merge: true,
        regex: '<\\!--',
        next: 'comment'
      }
    ],
    comment: [
      {
        token: 'comment',
        regex: '.*?-->',
        next: 'start'
      }, {
        token: 'comment',
        merge: true,
        regex: '.+'
      }
    ],
    nowiki: [
      {
        token: 'variable.language',
        regex: /<\/nowiki>/,
        next: 'start'
      },
      {
        token: 'comment',
        regex: /./
      }
    ],
    code: [
      {
        token: 'variable.language',
        regex: /<\/code>/,
        next: 'start'
      },
      {
        token: 'comment',
        regex: /./
      }
    ],
    pre: [
      {
        token: 'variable.language',
        regex: /<\/pre>/,
        next: 'start'
      },
      {
        token: 'comment',
        regex: /./
      }
    ],
    space: [
      {
        token: 'text',
        regex: '\\s+'
      }
    ],
    fx_version_os_version: [
      {
        token: ['markup.italic'],
        regex: /((?:,\s?)?(?:not\s)?(?:(?:win(?:xp|7|8)?|mac|linux|android|maemo)|=?(?:fx|tb|m)\d*))+/,
        next: 'close_tag'
      },
      {
        token: 'variable.language',
        regex: /\{\/for\}/
      }
    ],
    close_tag: [
      {
        token: 'variable.language',
        regex: /\}/,
        next: 'start'
      }
    ]
  });
})();
