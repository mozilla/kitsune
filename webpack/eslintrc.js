module.exports = {
    "env": {
        "es6": true,
        "browser": true
    },
    "ecmaFeatures": {
        "modules": true
    },
    "rules": {
        "no-undef": 2
    },
    "globals": {
        // globals exposed in webpack/global-expose-rules.js
        "_": "readonly",
        "nunjucks": "readonly",
        "CodeMirror": "readonly",
        "Rickshaw": "readonly",
        "detailsInit": "readonly",
        "tabsInit": "readonly",
        "Mozilla": "readonly",
        "trackEvent": "readonly",
        "_dntEnabled": "readonly",
        "URLify": "readonly",
        "dialogSet": "readonly",
        "$": "readonly",
        "jQuery": "readonly",
        "diff_match_patch": "readonly",
        "DIFF_DELETE": "readonly",
        "DIFF_INSERT": "readonly",
        "DIFF_EQUAL": "readonly",
        // globals exposed through explicit definition under `window.`
        "k": "readonly",
        "gettext": "readonly",
        "interpolate": "readonly",
        "Mzp": "readonly",
        "KBox": "readonly",
        "BrowserDetect": "readonly",
        "Modernizr": "readonly",
        "Marky": "readonly",
        "AAQSystemInfo": "readonly",
        "remoteTroubleshooting": "readonly",
        "d3": "readonly",
        "abs_y": "readonly",
        // global references, not exposed by anything, mostly here to keep eslint quiet
        "_gaq": "readonly",
        "RICKSHAW_NO_COMPAT": "readonly",
        "module": "readonly",
        "require": "readonly",
        "define": "readonly",
        "d": "readonly",
    }
}
