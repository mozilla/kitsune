import assert from "node:assert/strict";
import path from "node:path";
import { describe, test } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import postcss from "postcss";
import * as sass from "sass";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const scssDir = path.join(root, "kitsune/sumo/static/sumo/scss");
const nodeModules = path.join(root, "node_modules");
const loadPaths = [nodeModules, path.join(nodeModules, "@mozilla-protocol/core")];

function compile(body) {
    const source = `@use 'config/themes/tokens';\n${body}`;
    return sass.compileString(source, {
        url: pathToFileURL(path.join(scssDir, "fixture.scss")),
        loadPaths,
        style: "expanded",
    }).css;
}

function assertSassError(body, pattern) {
    assert.throws(
        () => compile(body),
        (error) => {
            assert.ok(error instanceof sass.Exception, `expected a Sass error, got ${error}`);
            assert.match(error.sassMessage, pattern);
            return true;
        },
    );
}

function customPropertyNames(rule) {
    return rule.nodes
        .filter((node) => node.type === "decl" && node.prop.startsWith("--"))
        .map((decl) => decl.prop)
        .sort();
}

describe("assert-same-keys", () => {
    test("reports a key missing from the dark map", () => {
        assertSassError(
            `@include tokens.assert-same-keys(
                ('page-bg': white, 'only-in-light': white),
                ('page-bg': black)
            );`,
            /missing from \$dark \(config\/themes\/_dark\.scss\): only-in-light/,
        );
    });

    test("reports a key missing from the light map", () => {
        assertSassError(
            `@include tokens.assert-same-keys(
                ('page-bg': white),
                ('page-bg': black, 'only-in-dark': black)
            );`,
            /missing from \$light \(config\/themes\/_light\.scss\): only-in-dark/,
        );
    });

    test("compiles without output when both maps have the same keys", () => {
        const css = compile(`
            @include tokens.assert-same-keys(
                ('page-bg': white, 'color-text': black),
                ('color-text': white, 'page-bg': black)
            );
        `);
        assert.equal(css, "");
    });

    test("rejects a light theme that is not a map", () => {
        assertSassError(
            `@include tokens.assert-same-keys('page-bg', ('page-bg': black));`,
            /\$light must be a map/,
        );
    });

    test("rejects a dark theme that is not a map", () => {
        assertSassError(
            `@include tokens.assert-same-keys(('page-bg': white), null);`,
            /\$dark must be a map/,
        );
    });

    test("rejects two empty maps", () => {
        assertSassError(`@include tokens.assert-same-keys((), ());`, /Both theme maps are empty/);
    });
});

describe("emit-theme", () => {
    test("emits one custom property per map entry", () => {
        const css = compile(`
            .theme {
                @include tokens.emit-theme(('page-bg': white, 'color-text': var(--color-ink-01)));
            }
        `);
        assert.equal(css, ".theme {\n  --page-bg: white;\n  --color-text: var(--color-ink-01);\n}");
    });

    test("emits a comma-separated list value unchanged", () => {
        const css = compile(`
            .theme {
                @include tokens.emit-theme((
                    'focus-shadow': (0 0 0 4px rgba(0, 96, 223, 0.3), 0 0 0 2px rgb(0, 138, 234)),
                ));
            }
        `);
        assert.equal(
            css,
            ".theme {\n  --focus-shadow: 0 0 0 4px rgba(0, 96, 223, 0.3), 0 0 0 2px rgb(0, 138, 234);\n}",
        );
    });

    test("rejects a theme that is not a map", () => {
        assertSassError(`.theme { @include tokens.emit-theme('page-bg'); }`, /emit-theme expects a map/);
    });

    for (const [label, value] of [
        ["null", "null"],
        ["an empty string", "''"],
        ["an empty list", "()"],
    ]) {
        test(`rejects ${label} as a value and names the key`, () => {
            assertSassError(
                `.theme { @include tokens.emit-theme(('page-bg': white, 'broken-token': ${value})); }`,
                /broken-token/,
            );
        });
    }
});

describe("theme entry point", () => {
    test("the dark theme and the print fallback define the same tokens", () => {
        const css = sass.compile(path.join(scssDir, "_theme.scss"), { loadPaths, style: "expanded" }).css;
        const darkRules = [];
        postcss.parse(css).walkRules((rule) => {
            if (rule.selector.replace(/["']/g, "") === "[data-theme=dark]") {
                darkRules.push(rule);
            }
        });
        const dark = darkRules.find((rule) => rule.parent.type === "root");
        const print = darkRules.find(
            (rule) => rule.parent.type === "atrule" && rule.parent.name === "media" && rule.parent.params === "print",
        );
        assert.ok(dark, "no top-level [data-theme=dark] rule");
        assert.ok(print, "no [data-theme=dark] rule inside @media print");

        const darkNames = customPropertyNames(dark);
        assert.ok(darkNames.length > 0, "the dark theme defines no tokens");
        assert.deepEqual(darkNames, customPropertyNames(print));
    });

    test("the Protocol bridge follows the theme :root and points each Protocol property at a token the theme defines", () => {
        const css = sass.compile(path.join(scssDir, "_theme.scss"), { loadPaths, style: "expanded" }).css;
        const rootRules = [];
        postcss.parse(css).walkRules((rule) => {
            if (rule.selector === ":root" && rule.parent.type === "root") {
                rootRules.push(rule);
            }
        });
        const themeRoot = rootRules.find((rule) => customPropertyNames(rule).includes("--page-bg"));
        const bridge = rootRules.at(-1);
        assert.ok(themeRoot, "no theme :root rule");
        assert.notEqual(bridge, themeRoot, "the bridge :root rule must come after the theme :root rule");

        assert.deepEqual(
            customPropertyNames(bridge),
            [
                "--background-color",
                "--background-color-inverse",
                "--background-color-secondary",
                "--background-color-secondary-inverse",
                "--background-color-tertiary",
                "--background-color-tertiary-inverse",
                "--body-text-color",
                "--body-text-color-inverse",
                "--body-text-color-secondary",
                "--body-text-color-secondary-inverse",
                "--link-color",
                "--link-color-hover",
                "--link-color-hover-inverse",
                "--link-color-inverse",
                "--link-color-visited",
                "--link-color-visited-inverse",
                "--title-text-color",
                "--title-text-color-inverse",
            ],
        );

        const themeTokens = customPropertyNames(themeRoot);
        for (const decl of bridge.nodes) {
            const token = /^var\((--[\w-]+)\)$/.exec(decl.value)?.[1];
            assert.ok(token, `${decl.prop} must be a plain var() reference, got ${decl.value}`);
            assert.ok(themeTokens.includes(token), `${decl.prop} points at ${token}, which the theme does not define`);
        }
    });
});
