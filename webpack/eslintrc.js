module.exports = {
    "extends": [
        "plugin:import/recommended",
    ],
    "settings": {
        "import/resolver": {
            "webpack": {
                "config": "./webpack.common.js",
            },
        },
    },
    "env": {
        "es6": true,
        "browser": true
    },
    "parserOptions": {
        "ecmaVersion": "latest",
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
        // unavoidable globals, due to library constraints or ubiquity
        "Mzp": "readonly",
        "$": "readonly",
        "jQuery": "readonly",
        "gettext": "readonly",
        "interpolate": "readonly",
        // global references, not exposed by anything, mostly here to keep eslint quiet
        "Mozilla": "readonly",
        "_gaq": "readonly",
        "RICKSHAW_NO_COMPAT": "readonly",
        "d": "readonly",
    }
}
