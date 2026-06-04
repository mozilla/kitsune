import importPlugin, { createNodeResolver } from "eslint-plugin-import-x";

export default [
    {
        files: ["webpack/**/*.{js,ts,jsx,tsx}", "svelte/**/*.{js,ts,jsx,tsx}"],
        ignores: ["**/tests/**"],
        plugins: {
            "import-x": importPlugin,
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
            "import-x/resolver-next": [
                createNodeResolver({
                    extensions: [".mjs", ".js", ".svelte"],
                }),
            ],
        },
        rules: {
            "no-undef": 2,
            "import-x/extensions": ["error", "ignorePackages", { svelte: "always" }],
            "import-x/first": 2,
            "import-x/no-self-import": 2,
            "import-x/no-cycle": 2,
        },
    },
]; 