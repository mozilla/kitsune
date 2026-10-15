import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

import postcss from "postcss";

const here = path.dirname(fileURLToPath(import.meta.url));
const defaultDist = path.join(here, "../../dist");
const defaultPairs = path.join(here, "contrast-pairs.json");

const THEMES = ["light", "dark"];
const MIN_RATIOS = [3, 4.5];
const CUSTOM_PROPERTY = /^--[^\s,()]+$/;
const NUMBER = /^[+-]?(?:\d+\.?\d*|\.\d+)%?$/;

export class ContrastError extends Error {
    name = "ContrastError";
}

export function parseColor(value) {
    const text = String(value).trim().toLowerCase();
    const unsupported = () => new ContrastError(`unsupported color "${value}"`);
    const keywords = {
        white: { r: 255, g: 255, b: 255, a: 1 },
        black: { r: 0, g: 0, b: 0, a: 1 },
        transparent: { r: 0, g: 0, b: 0, a: 0 },
    };
    if (Object.hasOwn(keywords, text)) return { ...keywords[text] };

    const hex = text.match(/^#([0-9a-f]+)$/)?.[1];
    if (hex && [3, 4, 6, 8].includes(hex.length)) {
        const digits = hex.length <= 4 ? [...hex].map((digit) => digit + digit).join("") : hex;
        const [r, g, b, a = 255] = digits.match(/../g).map((pair) => parseInt(pair, 16));
        return { r, g, b, a: a / 255 };
    }

    const body = text.match(/^rgba?\((.*)\)$/s)?.[1].trim();
    if (body === undefined) throw unsupported();

    let parts;
    if (body.includes(",")) {
        if (body.includes("/")) throw unsupported();
        parts = body.split(",").map((part) => part.trim());
    } else {
        const [channels, ...slashed] = body.split("/").map((part) => part.trim());
        parts = channels.split(/\s+/);
        if (parts.length !== 3 || slashed.length > 1) throw unsupported();
        parts.push(...slashed);
    }
    if (parts.length < 3 || parts.length > 4 || !parts.every((part) => NUMBER.test(part))) throw unsupported();

    const clamp = (number, max) => Math.min(Math.max(number, 0), max);
    const channel = (part) => Math.round(clamp(part.endsWith("%") ? (parseFloat(part) * 255) / 100 : parseFloat(part), 255));
    const alpha = (part) => clamp(part.endsWith("%") ? parseFloat(part) / 100 : parseFloat(part), 1);
    return { r: channel(parts[0]), g: channel(parts[1]), b: channel(parts[2]), a: parts.length === 4 ? alpha(parts[3]) : 1 };
}

function loadThemes(css) {
    let stylesheet;
    try {
        stylesheet = postcss.parse(css);
    } catch (error) {
        throw new ContrastError(`cannot parse the stylesheet: ${error.reason ?? error.message}`);
    }

    const light = new Map();
    const dark = new Map();
    let sawRoot = false;
    let sawDark = false;
    // Only top-level rules count: at-rules such as the print fallback never decide the on-screen theme.
    for (const rule of stylesheet.nodes) {
        if (rule.type !== "rule") continue;
        const selectors = rule.selectors.map((selector) => selector.replace(/["'\s]/g, ""));
        const isRoot = selectors.includes(":root");
        const isDark = selectors.includes("[data-theme=dark]");
        if (!isRoot && !isDark) continue;
        sawRoot ||= isRoot;
        sawDark ||= isDark;
        for (const decl of rule.nodes) {
            if (decl.type !== "decl" || !decl.prop.startsWith("--")) continue;
            if (decl.important) throw new ContrastError(`${decl.prop} is declared !important; the checker cannot model it`);
            // :root and [data-theme=dark] have equal specificity, so source order decides in dark.
            if (isRoot) light.set(decl.prop, decl.value);
            dark.set(decl.prop, decl.value);
        }
    }
    if (!sawRoot) throw new ContrastError("no top-level :root rule found in the stylesheet");
    if (!sawDark) throw new ContrastError("no top-level [data-theme=dark] rule found in the stylesheet");
    return { light, dark };
}

// Returns null for the guaranteed-invalid value: an undefined property, `initial`, or a var() with nothing to fall back on.
function resolveToken(name, theme, trail = []) {
    if (trail.includes(name)) throw new ContrastError(`cycle: ${[...trail, name].join(" -> ")}`);
    const raw = theme.get(name);
    if (raw === undefined || /^initial$/i.test(raw.trim())) return null;
    return substituteVars(raw, theme, [...trail, name]);
}

function substituteVars(value, theme, trail) {
    const malformed = () => new ContrastError(`malformed var() in "${value}"`);
    const pattern = /(?<![\w-])var\(/g;
    let result = "";
    let cursor = 0;
    for (let match; (match = pattern.exec(value)); ) {
        const open = match.index + match[0].length;
        let depth = 1;
        let end = open;
        for (; end < value.length && depth > 0; end++) {
            if (value[end] === "(") depth++;
            else if (value[end] === ")") depth--;
        }
        if (depth > 0) throw malformed();

        const inner = value.slice(open, end - 1);
        const comma = inner.indexOf(",");
        const name = (comma === -1 ? inner : inner.slice(0, comma)).trim();
        if (!CUSTOM_PROPERTY.test(name)) throw malformed();

        let replacement = resolveToken(name, theme, trail);
        if (replacement === null && comma !== -1) replacement = substituteVars(inner.slice(comma + 1).trim(), theme, trail);
        if (replacement === null) return null;

        result += value.slice(cursor, match.index) + replacement;
        cursor = end;
        pattern.lastIndex = end;
    }
    return result + value.slice(cursor);
}

function resolveColor(token, theme) {
    if (!theme.has(token)) throw new ContrastError(`${token} is not defined`);
    const value = resolveToken(token, theme);
    if (value === null) throw new ContrastError(`no value for ${token}`);
    try {
        return parseColor(value);
    } catch (error) {
        throw new ContrastError(`${token}: ${error.message}`);
    }
}

// The bottom color is always opaque here, so the result is too; channels round to 8 bits as a browser paints them.
function over(top, bottom) {
    const mix = (key) => Math.round(top[key] * top.a + bottom[key] * (1 - top.a));
    return { r: mix("r"), g: mix("g"), b: mix("b"), a: 1 };
}

function luminance({ r, g, b }) {
    const [red, green, blue] = [r, g, b].map((channel) => {
        const srgb = channel / 255;
        return srgb <= 0.04045 ? srgb / 12.92 : ((srgb + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

export function validateConfig(config) {
    const fail = (where, message) => {
        throw new ContrastError(`${where}: ${message}`);
    };
    const isObject = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
    const isToken = (value) => typeof value === "string" && CUSTOM_PROPERTY.test(value);
    const rejectUnknownKeys = (object, allowed, where) => {
        for (const key of Object.keys(object)) {
            if (!allowed.includes(key)) fail(where, `unknown key "${key}"`);
        }
    };

    if (!isObject(config)) throw new ContrastError("pairs file must be an object");
    rejectUnknownKeys(config, ["pairs", "exceptions"], "pairs file");
    const { pairs, exceptions = [] } = config;
    if (!Array.isArray(pairs) || pairs.length === 0) fail("pairs file", "pairs must be a non-empty array");
    if (!Array.isArray(exceptions)) fail("pairs file", "exceptions must be an array");

    const declared = new Map();
    pairs.forEach((pair, index) => {
        const where = `pairs[${index}]`;
        if (!isObject(pair)) throw new ContrastError(`${where} must be an object`);
        rejectUnknownKeys(pair, ["fg", "bg", "backdrop", "min", "themes"], where);
        if (!isToken(pair.fg)) fail(where, "fg must be a custom property name");
        if (!isToken(pair.bg)) fail(where, "bg must be a custom property name");
        if (pair.backdrop !== undefined && !isToken(pair.backdrop)) fail(where, "backdrop must be a custom property name");
        if (!MIN_RATIOS.includes(pair.min)) fail(where, `min must be ${MIN_RATIOS.join(" or ")}`);
        const { themes } = pair;
        if (
            !Array.isArray(themes) ||
            themes.length === 0 ||
            new Set(themes).size !== themes.length ||
            !themes.every((theme) => THEMES.includes(theme))
        ) {
            fail(where, `themes must be a non-empty list of unique theme names (${THEMES.join(", ")})`);
        }
        for (const theme of themes) {
            const key = `${pair.fg}|${pair.bg}|${theme}`;
            if (declared.has(key)) fail(where, `duplicate of pairs[${declared.get(key)}]`);
            declared.set(key, index);
        }
    });

    const excepted = new Map();
    exceptions.forEach((exception, index) => {
        const where = `exceptions[${index}]`;
        if (!isObject(exception)) throw new ContrastError(`${where} must be an object`);
        rejectUnknownKeys(exception, ["fg", "bg", "theme", "reason"], where);
        if (!isToken(exception.fg)) fail(where, "fg must be a custom property name");
        if (!isToken(exception.bg)) fail(where, "bg must be a custom property name");
        if (exception.theme === "dark") fail(where, "dark failures cannot be excepted; fix the dark token");
        if (exception.theme !== "light") fail(where, "theme must be light");
        if (typeof exception.reason !== "string" || exception.reason.trim() === "") {
            fail(where, "reason must be a non-empty string");
        }
        const key = `${exception.fg}|${exception.bg}|${exception.theme}`;
        if (!declared.has(key)) {
            fail(where, `matches no declared pair (${exception.fg} on ${exception.bg}, ${exception.theme})`);
        }
        if (excepted.has(key)) fail(where, `duplicate of exceptions[${excepted.get(key).index}]`);
        excepted.set(key, { index, exception });
    });

    return { pairs, excepted };
}

export function checkContrast(css, config) {
    const { pairs, excepted } = validateConfig(config);
    const themes = loadThemes(css);
    const results = [];

    for (const pair of pairs) {
        for (const themeName of pair.themes) {
            const theme = themes[themeName];
            const result = { fg: pair.fg, bg: pair.bg, theme: themeName, min: pair.min };
            try {
                const fg = resolveColor(pair.fg, theme);
                const bg = resolveColor(pair.bg, theme);
                const backdrop = pair.backdrop === undefined ? null : resolveColor(pair.backdrop, theme);
                if (backdrop && backdrop.a < 1) throw new ContrastError(`backdrop ${pair.backdrop} is translucent`);

                let surface = bg;
                if (bg.a < 1) {
                    if (!backdrop) throw new ContrastError(`${pair.bg} is translucent and the pair declares no backdrop`);
                    surface = over(bg, backdrop);
                }
                const ink = fg.a < 1 ? over(fg, surface) : fg;

                const [lighter, darker] = [luminance(ink), luminance(surface)].sort((a, b) => b - a);
                result.ratio = (lighter + 0.05) / (darker + 0.05);
            } catch (error) {
                if (!(error instanceof ContrastError)) throw error;
                results.push({ ...result, status: "ERROR", message: error.message });
                continue;
            }

            const known = excepted.get(`${pair.fg}|${pair.bg}|${themeName}`)?.exception;
            if (known) result.exception = known;
            const passes = result.ratio >= pair.min;
            result.status = passes ? (known ? "STALE" : "PASS") : known ? "EXCEPTION" : "FAIL";
            results.push(result);
        }
    }
    return results;
}

export function findStylesheet(distDir) {
    let names;
    try {
        names = fs.readdirSync(distDir);
    } catch (error) {
        throw new ContrastError(`cannot read ${distDir}: ${error.message}`);
    }
    const matches = names.filter((name) => /^screen.*\.css$/.test(name)).sort();
    if (matches.length === 0) {
        throw new ContrastError(`no screen*.css found in ${distDir}; build the frontend first (npm run webpack:build)`);
    }
    if (matches.length > 1) {
        throw new ContrastError(`expected exactly one screen*.css in ${distDir}, found ${matches.length}: ${matches.join(", ")}`);
    }
    return path.join(distDir, matches[0]);
}

export function run(argv, { log = console.log, error = console.error, distDir = defaultDist } = {}) {
    let results;
    try {
        let args;
        try {
            args = parseArgs({ args: argv, options: { pairs: { type: "string" } }, allowPositionals: true });
        } catch (parseError) {
            throw new ContrastError(parseError.message);
        }
        if (args.positionals.length > 1) {
            throw new ContrastError("usage: check-contrast.mjs [path/to/screen.css] [--pairs path/to/pairs.json]");
        }

        const load = (file, parse) => {
            try {
                return parse(fs.readFileSync(file, "utf8"));
            } catch (loadError) {
                throw new ContrastError(`cannot read ${file}: ${loadError.message}`);
            }
        };
        const css = load(args.positionals[0] ?? findStylesheet(distDir), (text) => text);
        const config = load(args.values.pairs ?? defaultPairs, JSON.parse);
        results = checkContrast(css, config);
    } catch (caught) {
        if (!(caught instanceof ContrastError)) throw caught;
        error(`check-contrast: ${caught.message}`);
        return 1;
    }

    const counts = { PASS: 0, EXCEPTION: 0, FAIL: 0, ERROR: 0, STALE: 0 };
    const notPassing = [];
    for (const result of results) {
        counts[result.status]++;
        const head = `${result.status.padEnd(9)} ${result.theme.padEnd(5)} ${result.fg} on ${result.bg}`;
        let line;
        if (result.status === "ERROR") {
            line = `${head}  ${result.message}`;
        } else {
            line = `${head}  ${result.ratio.toFixed(2)}:1 (min ${result.min})`;
            if (result.status === "EXCEPTION") {
                line += `  ${result.exception.reason}`;
            } else if (result.status === "STALE") {
                line += "  exception is stale: the pair now passes, remove it from exceptions";
            }
        }
        log(line);
        if (result.status !== "PASS") notPassing.push(line);
    }
    log(
        `${results.length} checks: ${counts.PASS} passed, ${counts.EXCEPTION} excepted, ` +
            `${counts.FAIL} failed, ${counts.ERROR} errors, ${counts.STALE} stale`,
    );
    for (const line of notPassing) log(line);
    return counts.FAIL + counts.ERROR + counts.STALE > 0 ? 1 : 0;
}

if (process.argv[1] && fs.realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)) {
    process.exitCode = run(process.argv.slice(2));
}
