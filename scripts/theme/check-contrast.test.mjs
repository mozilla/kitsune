import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { after, describe, test } from "node:test";
import { fileURLToPath } from "node:url";

import { ContrastError, checkContrast, findStylesheet, parseColor, run, validateConfig } from "./check-contrast.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const script = path.join(here, "check-contrast.mjs");
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "check-contrast-"));
after(() => fs.rmSync(tmp, { recursive: true, force: true }));

function stylesheet({ light = "", dark = "" }) {
    return `:root { ${light} }\n[data-theme=dark] { ${dark} }`;
}

function pair(overrides = {}) {
    return { fg: "--fg", bg: "--bg", min: 4.5, themes: ["light", "dark"], ...overrides };
}

function exception(overrides = {}) {
    return { fg: "--fg", bg: "--bg", theme: "light", reason: "pre-existing", ...overrides };
}

function ratioOf(css, overrides = {}) {
    const [result] = checkContrast(css, { pairs: [pair({ themes: ["light"], ...overrides })] });
    assert.notEqual(result.status, "ERROR", result.message);
    return result.ratio;
}

function execute(args) {
    const lines = [];
    const errors = [];
    const exitCode = run(args, { log: (line) => lines.push(line), error: (line) => errors.push(line) });
    return { exitCode, output: lines.join("\n"), errors: errors.join("\n") };
}

function writeFixture(name, css, config) {
    const dir = fs.mkdtempSync(path.join(tmp, `${name}-`));
    const cssPath = path.join(dir, "screen.css");
    const pairsPath = path.join(dir, "pairs.json");
    fs.writeFileSync(cssPath, css);
    fs.writeFileSync(pairsPath, JSON.stringify(config));
    return [cssPath, "--pairs", pairsPath];
}

const readable = stylesheet({ light: "--fg: #000; --bg: #fff;", dark: "--fg: #fff; --bg: #000;" });
const unreadable = stylesheet({ light: "--fg: #777; --bg: #fff;", dark: "--fg: #fff; --bg: #000;" });

describe("parseColor", () => {
    test("parses hex in 3, 4, 6 and 8 digit forms", () => {
        assert.deepEqual(parseColor("#fff"), { r: 255, g: 255, b: 255, a: 1 });
        assert.deepEqual(parseColor("#0f08"), { r: 0, g: 255, b: 0, a: 0x88 / 255 });
        assert.deepEqual(parseColor("#0060DF"), { r: 0, g: 96, b: 223, a: 1 });
        assert.deepEqual(parseColor(" #0060df80 "), { r: 0, g: 96, b: 223, a: 0x80 / 255 });
    });

    test("parses rgb() and rgba() in comma and space syntax", () => {
        const opaque = { r: 0, g: 96, b: 223, a: 1 };
        const tinted = { r: 0, g: 96, b: 223, a: 0.08 };
        assert.deepEqual(parseColor("rgb(0, 96, 223)"), opaque);
        assert.deepEqual(parseColor("RGB(0,96,223)"), opaque);
        assert.deepEqual(parseColor("rgb(0 96 223)"), opaque);
        assert.deepEqual(parseColor("rgba(0, 96, 223, 0.08)"), tinted);
        assert.deepEqual(parseColor("rgb(0 96 223 / 0.08)"), tinted);
        assert.deepEqual(parseColor("rgba(0 96 223 / 8%)"), tinted);
        assert.deepEqual(parseColor("rgb(0% 100% 50%)"), { r: 0, g: 255, b: 128, a: 1 });
    });

    test("rounds channels to 8 bits and keeps alpha fractional", () => {
        assert.deepEqual(parseColor("rgb(1.4 1.5 254.5)"), { r: 1, g: 2, b: 255, a: 1 });
        assert.deepEqual(parseColor("rgba(1.4, 1.5, 0, 0.123)"), { r: 1, g: 2, b: 0, a: 0.123 });
    });

    test("parses white, black and transparent", () => {
        assert.deepEqual(parseColor("white"), { r: 255, g: 255, b: 255, a: 1 });
        assert.deepEqual(parseColor("BLACK"), { r: 0, g: 0, b: 0, a: 1 });
        assert.deepEqual(parseColor("transparent"), { r: 0, g: 0, b: 0, a: 0 });
    });

    test("clamps out-of-range channels and alpha like CSS", () => {
        assert.deepEqual(parseColor("rgb(300, -5, 0, 2)"), { r: 255, g: 0, b: 0, a: 1 });
    });

    for (const value of [
        "rebeccapurple",
        "currentcolor",
        "hsl(0 0% 0%)",
        "color-mix(in srgb, red, blue)",
        "var(--x)",
        "#12",
        "#12345",
        "#ggg",
        "rgb(0, 96)",
        "rgb(0, 96, 223, 0.5, 1)",
        "rgb(0 96, 223)",
        "rgb(0, 96, 223 / 0.5)",
        "rgb(0 96 223 / 0.5 / 1)",
        "rgb(none 0 0)",
        "rgb(NaN, 0, 0)",
        "rgb(Infinity, 0, 0)",
        "rgb(1e3, 0, 0)",
        "",
    ]) {
        test(`rejects ${JSON.stringify(value)}`, () => {
            assert.throws(() => parseColor(value), (error) => {
                assert.ok(error instanceof ContrastError, `expected ContrastError, got ${error}`);
                assert.match(error.message, /unsupported color/);
                return true;
            });
        });
    }
});

describe("custom property resolution", () => {
    test("resolves a var() chain through two levels", () => {
        const css = stylesheet({ light: "--fg: var(--mid); --mid: var(--base); --base: #000; --bg: #fff;" });
        assert.equal(ratioOf(css), 21);
    });

    test("a dark value overrides the light value for the dark theme only", () => {
        const css = stylesheet({ light: "--fg: #000; --bg: #fff;", dark: "--fg: #777;" });
        const [light, dark] = checkContrast(css, { pairs: [pair()] });
        assert.deepEqual([light.theme, light.ratio.toFixed(2)], ["light", "21.00"]);
        assert.deepEqual([dark.theme, dark.ratio.toFixed(2)], ["dark", "4.48"]);
    });

    test("merges every top-level :root block with the last declaration winning", () => {
        const css = [
            ":root { --fg: #fff; --bg: #fff; }",
            ":root { --fg: #000; }",
            "[data-theme=dark] { --x: #000; }",
        ].join("\n");
        assert.equal(ratioOf(css), 21);
    });

    test("matches [data-theme=\"dark\"] written with quotes", () => {
        const css = ':root { --fg: #000; --bg: #fff; }\n[data-theme="dark"] { --fg: #fff; --bg: #000; }';
        const [, dark] = checkContrast(css, { pairs: [pair()] });
        assert.equal(dark.ratio, 21);
    });

    test("ignores :root and dark rules nested in at-rules", () => {
        const css = [
            ":root { --fg: #000; --bg: #fff; }",
            "[data-theme=dark] { --fg: #fff; --bg: #000; }",
            "@media print { [data-theme=dark] { --fg: #fff; --bg: #fff; } :root { --fg: #fff; } }",
        ].join("\n");
        const results = checkContrast(css, { pairs: [pair()] });
        assert.deepEqual(results.map((result) => result.ratio), [21, 21]);
    });

    test("a :root block after the dark rule wins in dark too, as equal specificity does in a browser", () => {
        const css = [
            ":root { --fg: #000; --bg: #fff; }",
            "[data-theme=dark] { --fg: #fff; --bg: #000; }",
            ":root { --fg: #777; }",
        ].join("\n");
        const [light, dark] = checkContrast(css, { pairs: [pair()] });
        assert.equal(light.ratio.toFixed(2), "4.48");
        assert.equal(dark.ratio.toFixed(2), "4.69");
    });

    test("uses the var() fallback when the property is undefined or initial", () => {
        const css = stylesheet({
            light: "--fg: var(--missing, var(--base)); --bg: var(--off, #fff); --off: initial; --base: #000;",
        });
        assert.equal(ratioOf(css), 21);
    });

    test("reports a token whose light value is initial as having no value", () => {
        const css = stylesheet({ light: "--fg: initial; --bg: #fff;", dark: "--fg: #000;" });
        const [light, dark] = checkContrast(css, { pairs: [pair()] });
        assert.equal(light.status, "ERROR");
        assert.match(light.message, /no value for --fg/);
        assert.equal(dark.status, "PASS");
    });

    test("reports a var() with no value and no fallback as having no value", () => {
        const css = stylesheet({ light: "--fg: var(--missing); --bg: #fff;" });
        const [light] = checkContrast(css, { pairs: [pair({ themes: ["light"] })] });
        assert.equal(light.status, "ERROR");
        assert.match(light.message, /no value for --fg/);
    });

    test("fails on a token that is not defined", () => {
        const css = stylesheet({ light: "--bg: #fff;" });
        const [light] = checkContrast(css, { pairs: [pair({ themes: ["light"] })] });
        assert.equal(light.status, "ERROR");
        assert.match(light.message, /--fg is not defined/);
    });

    test("fails closed on a cycle and names the chain", () => {
        const css = stylesheet({ light: "--fg: var(--a); --a: var(--b); --b: var(--a); --bg: #fff;" });
        const [light] = checkContrast(css, { pairs: [pair({ themes: ["light"] })] });
        assert.equal(light.status, "ERROR");
        assert.match(light.message, /cycle: --fg -> --a -> --b -> --a/);
    });

    test("fails closed on a self-referencing token", () => {
        const css = stylesheet({ light: "--fg: var(--fg, #000); --bg: #fff;" });
        const [light] = checkContrast(css, { pairs: [pair({ themes: ["light"] })] });
        assert.equal(light.status, "ERROR");
        assert.match(light.message, /cycle: --fg -> --fg/);
    });

    for (const [name, css] of Object.entries({
        "a :root": ":root { --fg: #000 !important; --bg: #fff; }\n[data-theme=dark] { --x: #000; }",
        "the dark rule": ":root { --fg: #000; --bg: #fff; }\n[data-theme=dark] { --fg: #fff !important; }",
    })) {
        test(`fails closed on an !important custom property in ${name}`, () => {
            assert.throws(() => checkContrast(css, { pairs: [pair()] }), (error) => {
                assert.ok(error instanceof ContrastError, `expected ContrastError, got ${error}`);
                assert.match(error.message, /--fg is declared !important/);
                return true;
            });
        });
    }

    test("ignores !important on ordinary properties and inside at-rules", () => {
        const css = [
            ":root { --fg: #000; --bg: #fff; color: red !important; }",
            "[data-theme=dark] { --fg: #fff; --bg: #000; }",
            "@media print { :root { --fg: #fff !important; } }",
        ].join("\n");
        assert.deepEqual(checkContrast(css, { pairs: [pair()] }).map((result) => result.status), ["PASS", "PASS"]);
    });

    test("fails closed on a malformed var()", () => {
        const css = stylesheet({ light: "--fg: var(foo, #000); --bg: #fff;" });
        const [light] = checkContrast(css, { pairs: [pair({ themes: ["light"] })] });
        assert.equal(light.status, "ERROR");
        assert.match(light.message, /malformed var\(\)/);
    });

    test("names the token and value of an unsupported color", () => {
        const css = stylesheet({ light: "--fg: var(--ink); --ink: rebeccapurple; --bg: #fff;" });
        const [light] = checkContrast(css, { pairs: [pair({ themes: ["light"] })] });
        assert.equal(light.status, "ERROR");
        assert.match(light.message, /--fg: unsupported color "rebeccapurple"/);
    });

    test("throws when the stylesheet has no :root or no dark rule", () => {
        assert.throws(() => checkContrast("[data-theme=dark] { --fg: #000; }", { pairs: [pair()] }), /no top-level :root/);
        assert.throws(() => checkContrast(":root { --fg: #000; }", { pairs: [pair()] }), /no top-level \[data-theme=dark\]/);
    });
});

describe("contrast ratio", () => {
    test("computes WCAG ratios with sRGB linearization", () => {
        assert.equal(ratioOf(stylesheet({ light: "--fg: #000; --bg: #fff;" })).toFixed(2), "21.00");
        assert.equal(ratioOf(stylesheet({ light: "--fg: #767676; --bg: #fff;" })).toFixed(2), "4.54");
        assert.equal(ratioOf(stylesheet({ light: "--fg: #fff; --bg: #767676;" })).toFixed(2), "4.54");
        assert.equal(ratioOf(stylesheet({ light: "--fg: #777; --bg: #fff;" })).toFixed(2), "4.48");
    });

    test("compares the unrounded ratio against min", () => {
        const css = stylesheet({ light: "--fg: rgb(112 121 114); --bg: #fff;" });
        const [result] = checkContrast(css, { pairs: [pair({ themes: ["light"] })] });
        assert.equal(result.ratio.toFixed(2), "4.50");
        assert.equal(result.status, "FAIL");
    });

    test("composites a translucent background over the backdrop before measuring", () => {
        const translucent = stylesheet({
            light: "--fg: #000; --bg: rgba(0, 0, 0, 0.2); --page: #fff;",
        });
        const solid = stylesheet({ light: "--fg: #000; --bg: #cccccc;" });
        assert.equal(ratioOf(translucent, { backdrop: "--page" }), ratioOf(solid));
    });

    test("composites a translucent foreground over the background", () => {
        const translucent = stylesheet({ light: "--fg: rgba(0, 0, 0, 0.8); --bg: #fff;" });
        const solid = stylesheet({ light: "--fg: #333333; --bg: #fff;" });
        assert.equal(ratioOf(translucent), ratioOf(solid));
    });

    test("composites the background over the backdrop first, then the foreground over the result", () => {
        const translucent = stylesheet({
            light: "--fg: rgba(255, 255, 255, 0.5); --bg: rgba(255, 255, 255, 0.5); --page: #000;",
        });
        const solid = stylesheet({ light: "--fg: #c0c0c0; --bg: #808080;" });
        assert.equal(ratioOf(translucent, { backdrop: "--page" }), ratioOf(solid));
    });

    test("rounds a composite to 8-bit channels as a browser paints it", () => {
        const translucent = stylesheet({ light: "--fg: #000; --bg: rgba(0, 0, 0, 0.5); --page: #fff;" });
        const solid = stylesheet({ light: "--fg: #000; --bg: #808080;" });
        assert.equal(ratioOf(translucent, { backdrop: "--page" }), ratioOf(solid));
    });

    test("fails closed on a translucent background without a backdrop", () => {
        const css = stylesheet({ light: "--fg: #000; --bg: rgba(0, 0, 0, 0.2);" });
        const [result] = checkContrast(css, { pairs: [pair({ themes: ["light"] })] });
        assert.equal(result.status, "ERROR");
        assert.match(result.message, /--bg is translucent and the pair declares no backdrop/);
    });

    test("fails closed on a translucent backdrop", () => {
        const css = stylesheet({ light: "--fg: #000; --bg: rgba(0, 0, 0, 0.2); --page: rgba(255, 255, 255, 0.5);" });
        const [result] = checkContrast(css, { pairs: [pair({ themes: ["light"], backdrop: "--page" })] });
        assert.equal(result.status, "ERROR");
        assert.match(result.message, /backdrop --page is translucent/);
    });
});

describe("pairs file validation", () => {
    const rejected = {
        "an unknown top-level key": [{ pairs: [pair()], exceptionz: [] }, /unknown key "exceptionz"/],
        "no pairs": [{ pairs: [] }, /pairs must be a non-empty array/],
        "pairs that is not an array": [{ pairs: pair() }, /pairs must be a non-empty array/],
        "an unknown pair key": [{ pairs: [pair({ theme: "light" })] }, /pairs\[0\]: unknown key "theme"/],
        "a missing fg": [{ pairs: [pair({ fg: undefined })] }, /pairs\[0\]: fg must be a custom property name/],
        "a bg that is not a custom property": [{ pairs: [pair({ bg: "white" })] }, /pairs\[0\]: bg must be a custom property name/],
        "a bad backdrop": [{ pairs: [pair({ backdrop: 3 })] }, /pairs\[0\]: backdrop must be a custom property name/],
        "a missing min": [{ pairs: [pair({ min: undefined })] }, /pairs\[0\]: min must be 3 or 4\.5/],
        "a string min": [{ pairs: [pair({ min: "4.5" })] }, /pairs\[0\]: min must be 3 or 4\.5/],
        "a min that weakens the bar": [{ pairs: [pair({ min: 2 })] }, /pairs\[0\]: min must be 3 or 4\.5/],
        "a null min": [{ pairs: [pair({ min: null })] }, /pairs\[0\]: min must be 3 or 4\.5/],
        "missing themes": [{ pairs: [pair({ themes: undefined })] }, /pairs\[0\]: themes must be/],
        "empty themes": [{ pairs: [pair({ themes: [] })] }, /pairs\[0\]: themes must be/],
        "themes that is a string": [{ pairs: [pair({ themes: "light" })] }, /pairs\[0\]: themes must be/],
        "an unknown theme": [{ pairs: [pair({ themes: ["sepia"] })] }, /pairs\[0\]: themes must be/],
        "a repeated theme": [{ pairs: [pair({ themes: ["light", "light"] })] }, /pairs\[0\]: themes must be/],
        "a duplicate pair": [{ pairs: [pair(), pair({ backdrop: "--page" })] }, /pairs\[1\]: duplicate of pairs\[0\]/],
        "a non-object pair": [{ pairs: ["--fg"] }, /pairs\[0\] must be an object/],
        "a non-object file": [[pair()], /pairs file must be an object/],
        "exceptions that is not an array": [{ pairs: [pair()], exceptions: {} }, /exceptions must be an array/],
        "an unknown exception key": [{ pairs: [pair()], exceptions: [exception({ why: "x" })] }, /exceptions\[0\]: unknown key "why"/],
        "an exception without a reason": [{ pairs: [pair()], exceptions: [exception({ reason: undefined })] }, /exceptions\[0\]: reason must be a non-empty string/],
        "an exception with a blank reason": [{ pairs: [pair()], exceptions: [exception({ reason: "  " })] }, /exceptions\[0\]: reason must be a non-empty string/],
        "an exception with a bad theme": [{ pairs: [pair()], exceptions: [exception({ theme: "sepia" })] }, /exceptions\[0\]: theme must be/],
        "an exception for the dark theme": [{ pairs: [pair()], exceptions: [exception({ theme: "dark" })] }, /exceptions\[0\]: dark failures cannot be excepted; fix the dark token/],
        "a duplicate exception": [{ pairs: [pair()], exceptions: [exception(), exception()] }, /exceptions\[1\]: duplicate of exceptions\[0\]/],
        "an exception matching no pair": [{ pairs: [pair()], exceptions: [exception({ fg: "--other" })] }, /exceptions\[0\]: matches no declared pair \(--other on --bg, light\)/],
        "an exception for a theme the pair does not cover": [{ pairs: [pair({ themes: ["dark"] })], exceptions: [exception()] }, /exceptions\[0\]: matches no declared pair/],
    };

    for (const [name, [config, pattern]] of Object.entries(rejected)) {
        test(`rejects ${name}`, () => {
            assert.throws(() => checkContrast(readable, config), (error) => {
                assert.ok(error instanceof ContrastError, `expected ContrastError, got ${error}`);
                assert.match(error.message, pattern);
                return true;
            });
        });
    }

    test("the shipped pairs file is valid", () => {
        const config = JSON.parse(fs.readFileSync(path.join(here, "contrast-pairs.json"), "utf8"));
        assert.ok(validateConfig(config).pairs.length > 0);
    });
});

describe("statuses", () => {
    test("a pair at or above min passes in both themes", () => {
        const results = checkContrast(readable, { pairs: [pair()] });
        assert.deepEqual(results.map((result) => [result.theme, result.status]), [["light", "PASS"], ["dark", "PASS"]]);
    });

    test("a failing pair is a FAIL", () => {
        const [light, dark] = checkContrast(unreadable, { pairs: [pair()] });
        assert.equal(light.status, "FAIL");
        assert.equal(dark.status, "PASS");
    });

    test("a failing pair listed as an exception is an EXCEPTION carrying its justification", () => {
        const [light] = checkContrast(unreadable, { pairs: [pair()], exceptions: [exception()] });
        assert.equal(light.status, "EXCEPTION");
        assert.equal(light.exception.reason, "pre-existing");
    });

    test("an exception for a pair that now passes is STALE", () => {
        const [light] = checkContrast(readable, { pairs: [pair()], exceptions: [exception()] });
        assert.equal(light.status, "STALE");
    });

    test("an exception does not cover the other theme of the same pair", () => {
        const css = stylesheet({ light: "--fg: #777; --bg: #fff;", dark: "--fg: #333; --bg: #000;" });
        const [light, dark] = checkContrast(css, { pairs: [pair()], exceptions: [exception()] });
        assert.equal(light.status, "EXCEPTION");
        assert.equal(dark.status, "FAIL");
    });

    test("an exception does not hide a resolution error", () => {
        const css = stylesheet({ light: "--fg: initial; --bg: #fff;", dark: "--fg: #fff; --bg: #000;" });
        const [light] = checkContrast(css, { pairs: [pair()], exceptions: [exception()] });
        assert.equal(light.status, "ERROR");
    });
});

describe("findStylesheet", () => {
    function distWith(...files) {
        const dir = fs.mkdtempSync(path.join(tmp, "dist-"));
        for (const file of files) fs.writeFileSync(path.join(dir, file), "");
        return dir;
    }

    test("returns the single dist/screen*.css", () => {
        const dir = distWith("screen.css", "screen.css.map", "other.css", "app.js");
        assert.equal(findStylesheet(dir), path.join(dir, "screen.css"));
    });

    test("matches a content-hashed name", () => {
        const dir = distWith("screen.0e44301d.css");
        assert.equal(findStylesheet(dir), path.join(dir, "screen.0e44301d.css"));
    });

    test("fails when there is no match and names the pattern", () => {
        const dir = distWith("other.css");
        assert.throws(() => findStylesheet(dir), (error) => {
            assert.ok(error instanceof ContrastError);
            assert.match(error.message, /no screen\*\.css found in /);
            assert.ok(error.message.includes(dir));
            return true;
        });
    });

    test("fails when the directory is missing", () => {
        assert.throws(() => findStylesheet(path.join(tmp, "nope")), ContrastError);
    });

    test("fails when several match and names them", () => {
        const dir = distWith("screen.css", "screen.old.css");
        assert.throws(() => findStylesheet(dir), (error) => {
            assert.ok(error instanceof ContrastError);
            assert.match(error.message, /expected exactly one screen\*\.css/);
            assert.ok(error.message.includes("screen.css") && error.message.includes("screen.old.css"));
            return true;
        });
    });
});

describe("run", () => {
    const passing = { pairs: [pair()] };

    test("a failing pair exits 1 and names both tokens and the ratio", () => {
        const { exitCode, output } = execute(writeFixture("fail", unreadable, passing));
        assert.equal(exitCode, 1);
        assert.match(output, /FAIL\s+light\s+--fg on --bg\s+4\.48:1 \(min 4\.5\)/);
        assert.match(output, /PASS\s+dark\s+--fg on --bg\s+21\.00:1 \(min 4\.5\)/);
    });

    test("the same failing pair listed as an exception exits 0", () => {
        const { exitCode, output } = execute(
            writeFixture("excepted", unreadable, { ...passing, exceptions: [exception({ reason: "legacy grey" })] }),
        );
        assert.equal(exitCode, 0);
        assert.match(output, /EXCEPTION\s+light\s+--fg on --bg\s+4\.48:1 \(min 4\.5\)\s+legacy grey$/m);
    });

    test("an exception for a pair that now passes is reported as stale and exits 1", () => {
        const { exitCode, output } = execute(writeFixture("stale", readable, { ...passing, exceptions: [exception()] }));
        assert.equal(exitCode, 1);
        assert.match(output, /STALE\s+light\s+--fg on --bg\s+21\.00:1 \(min 4\.5\)\s+exception is stale/);
    });

    test("all pairs passing exits 0", () => {
        const { exitCode, output } = execute(writeFixture("pass", readable, passing));
        assert.equal(exitCode, 0);
        assert.match(output, /2 checks: 2 passed, 0 excepted, 0 failed, 0 errors, 0 stale$/);
    });

    test("repeats every non-PASS line after the summary so it cannot hide among the passes", () => {
        const css = stylesheet({
            light: "--fg: #777; --ex-fg: #777; --ok-fg: #000; --ok2-fg: #000; --bg: #fff;",
            dark: "--x: #000;",
        });
        const light = { bg: "--bg", min: 4.5, themes: ["light"] };
        const config = {
            pairs: [
                { fg: "--fg", ...light },
                { fg: "--ex-fg", ...light },
                { fg: "--ok-fg", ...light },
                { fg: "--missing", ...light },
                { fg: "--ok2-fg", ...light },
            ],
            exceptions: [exception({ fg: "--ex-fg" }), exception({ fg: "--ok-fg" })],
        };
        const { exitCode, output } = execute(writeFixture("repeat", css, config));
        assert.equal(exitCode, 1);

        const lines = output.split("\n");
        const summary = lines.findIndex((line) => /^5 checks:/.test(line));
        const repeated = lines.slice(summary + 1);
        assert.deepEqual(repeated.map((line) => line.split(/\s+/)[0]), ["FAIL", "EXCEPTION", "STALE", "ERROR"]);
        for (const line of repeated) assert.ok(lines.slice(0, summary).includes(line), `${line} is not in the per-pair lines`);
    });

    test("an unresolvable pair prints the reason and exits 1", () => {
        const css = stylesheet({ light: "--fg: initial; --bg: #fff;", dark: "--fg: #fff; --bg: #000;" });
        const { exitCode, output } = execute(writeFixture("novalue", css, passing));
        assert.equal(exitCode, 1);
        assert.match(output, /ERROR\s+light\s+--fg on --bg\s+no value for --fg/);
    });

    test("a malformed pairs file prints the problem and exits 1", () => {
        const { exitCode, errors } = execute(writeFixture("malformed", readable, { pairs: [pair({ min: 2 })] }));
        assert.equal(exitCode, 1);
        assert.match(errors, /pairs\[0\]: min must be 3 or 4\.5/);
    });

    test("an exception matching no pair prints the problem and exits 1", () => {
        const { exitCode, errors } = execute(
            writeFixture("orphan", readable, { ...passing, exceptions: [exception({ bg: "--nowhere" })] }),
        );
        assert.equal(exitCode, 1);
        assert.match(errors, /matches no declared pair/);
    });

    test("an unreadable stylesheet, unparseable JSON, or missing files exit 1", () => {
        const [cssPath, flag, pairsPath] = writeFixture("broken", readable, passing);
        fs.writeFileSync(pairsPath, "{ not json");
        assert.equal(execute([cssPath, flag, pairsPath]).exitCode, 1);
        assert.equal(execute([path.join(tmp, "missing.css"), flag, pairsPath]).exitCode, 1);
        const [okCss, , okPairs] = writeFixture("ok", readable, passing);
        assert.equal(execute([okCss, flag, okPairs.replace("pairs.json", "missing.json")]).exitCode, 1);
        fs.writeFileSync(okCss, "this is { not css");
        assert.equal(execute([okCss, flag, okPairs]).exitCode, 1);
    });

    test("more than one positional argument exits 1", () => {
        const [cssPath, flag, pairsPath] = writeFixture("args", readable, passing);
        assert.equal(execute([cssPath, cssPath, flag, pairsPath]).exitCode, 1);
        assert.equal(execute([cssPath, "--bogus"]).exitCode, 1);
    });

    test("without a path it fails when dist has no single screen*.css", () => {
        const dir = fs.mkdtempSync(path.join(tmp, "empty-dist-"));
        const lines = [];
        const exitCode = run([], { distDir: dir, log: () => {}, error: (line) => lines.push(line) });
        assert.equal(exitCode, 1);
        assert.match(lines.join("\n"), /no screen\*\.css found/);
    });

    test("without a path it checks the single dist stylesheet", () => {
        const dir = fs.mkdtempSync(path.join(tmp, "one-dist-"));
        fs.writeFileSync(path.join(dir, "screen.css"), readable);
        const [, flag, pairsPath] = writeFixture("pairs-only", readable, passing);
        const lines = [];
        const exitCode = run([flag, pairsPath], { distDir: dir, log: (line) => lines.push(line), error: () => {} });
        assert.equal(exitCode, 0);
        assert.ok(lines.some((line) => line.startsWith("PASS")));
    });

    test("the CLI process exits with the same code", () => {
        const failing = spawnSync(process.execPath, [script, ...writeFixture("cli-fail", unreadable, passing)], { encoding: "utf8" });
        assert.equal(failing.status, 1);
        assert.match(failing.stdout, /FAIL\s+light\s+--fg on --bg\s+4\.48:1/);
        const ok = spawnSync(process.execPath, [script, ...writeFixture("cli-pass", readable, passing)], { encoding: "utf8" });
        assert.equal(ok.status, 0);
    });
});
