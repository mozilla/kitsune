import importPlugin from "eslint-plugin-import";

export default [
    {
        files: ["webpack/**/*.{js,ts,jsx,tsx}", "svelte/**/*.{js,ts,jsx,tsx}"],
        ignores: ["**/tests/**"],
        plugins: {
            import: importPlugin,
        },
        languageOptions: {
            ecmaVersion: "latest",
            sourceType: "module",
            globals: {
                // Browser globals
                document: "readonly",
                window: "readonly",
                // Node.js globals
                process: "readonly",
                global: "readonly",
                // Project-specific globals
                Mzp: "readonly",
                $: "readonly",
                jQuery: "readonly",
                gettext: "readonly",
                interpolate: "readonly",
                Mozilla: "readonly",
                _gaq: "readonly",
                RICKSHAW_NO_COMPAT: "readonly",
                d: "readonly",
            },
        },
        settings: {
            "import/resolver": {
                webpack: {
                    config: "./webpack.common.js",
                },
            },
        },
        rules: {
            "no-undef": 2,
            "import/extensions": 2,
            "import/first": 2,
            "import/no-self-import": 2,
            "import/no-cycle": 2,
        },
    },
]; 