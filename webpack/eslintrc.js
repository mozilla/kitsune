module.exports = {
    "extends": [
        "plugin:import/recommended",
    ],
    "settings": {
        "import/resolver": "webpack",
    },
    "env": {
        "es6": true,
        "browser": true
    },
    "parserOptions": {
        "ecmaVersion": 2021,
        "sourceType": "module",
    },
    "rules": {
        "no-undef": 2,
        "import/extensions": 2,
        "import/first": 2,
        "import/no-self-import": 2,
        "import/no-cycle": 2,
    },
    "ignorePatterns": [
        "**/tests/**",
    ],
    "globals": {
        // globals exposed in webpack/global-expose-rules.js
        "nunjucks": "readonly",
        "CodeMirror": "readonly",
        "detailsInit": "readonly",
        "tabsInit": "readonly",
        "trackEvent": "readonly",
        "$": "readonly",
        "jQuery": "readonly",
        "DIFF_DELETE": "readonly",
        "DIFF_INSERT": "readonly",
        "DIFF_EQUAL": "readonly",
        // globals exposed through explicit definition under `window.`
        "k": "readonly",
        "gettext": "readonly",
        "interpolate": "readonly",
        "Mzp": "readonly",
        "BrowserDetect": "readonly",
        "Modernizr": "readonly",
        "Marky": "readonly",
        "AAQSystemInfo": "readonly",
        "remoteTroubleshooting": "readonly",
        "d3": "readonly",
        "abs_y": "readonly",
        "ShowFor": "readonly",
        // global references, not exposed by anything, mostly here to keep eslint quiet
        "Mozilla": "readonly",
        "_gaq": "readonly",
        "RICKSHAW_NO_COMPAT": "readonly",
        "module": "readonly",
        "require": "readonly",
        "define": "readonly",
        "d": "readonly",
    }
}
