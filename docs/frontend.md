# Frontend Infrastructure

We use [Webpack](https://webpack.js.org/) to manage our frontend assets.
Its configuration lives in `webpack.config.js`,
which imports files from  the `webpack/` folder.

To build the development Webpack bundle run `npm run webpack:build`.
To watch files
(excluding the Webpack configuration files)
and automatically rebuild the development Webpack bundle when they change,
run `npm run webpack:watch`.

To build a production Webpack bundle run `npm run webpack:build:prod`.

Webpack puts its build output in the `dist/` folder,
which is picked up by Django staticfiles.

## Entry points

`webpack/entrypoints.js` defines each of our entry points,
and the files that should be bundled into them.

For now this is very verbose,
as it mirrors the configuration we used in our old Django Pipeline setup.
However over time we'll leverage the ability to import libraries directly in the JS files which require them,
reducing the number of files we need to list here.

When building a development bundle,
we generate sourcemaps to make in-browser debugging easier.

When building a production bundle,
we add a hash to the output file names,
to allow for cache-busting on staging and production.

### Loading in Django

We use the [HtmlWebpackPlugin](https://webpack.js.org/plugins/html-webpack-plugin/) to generate HTML files for each of our entry points,
which includes the script tags
(and link tags, explained in the CSS section below)
needed to load the hashed chunks that form each entry point.
This configuration lives in `webpack/entrypoints-html.js`.

In Django,
templates can set the `scripts` variable to specify which entry points should be loaded for that template.

### Loading CSS

There is a special entry point `screen` which contains all our CSS,
and is treated slightly differently by `webpack/entrypoints-html.js`.
Since Webpack is primarily a JS bundler it emits an empty JS file,
which we have no need to include in our site,
so `webpack/entrypoints-html.js` ignores it.

## Javascript

All our JS files are run through [Babel](https://babeljs.io/),
allowing us to use modern JS syntax now,
without having to worry whether our users' browsers support it.

Webpack automatically minifies our JS when building the production bundle.

### Globals

Because most of our JS stack was written well before modules were a thing,
many files place variables in the global scope for other files to use.
However in Webpack,
unless a file explicitly places a variable under `window`,
we have to expose each of those variables manually.

This is done in `webpack/global-expose-rules.js`.
Like above,
over time we'll leverage imports to reduce the number of variables we have to expose to the global scope.

## Stylesheets

Our stylesheets are written in [Sass](https://sass-lang.com/),
using its SCSS syntax (`.scss`).

We use the [MiniCssExtractPlugin](https://webpack.js.org/plugins/mini-css-extract-plugin/) to separate our CSS from our JS files.

### PostCSS

We use the [postcss-loader](https://webpack.js.org/loaders/postcss-loader/) to process our css files with postcss.
Its configuration lives in `postcss.config.js`.

When building a production bundle,
[cssnano](https://cssnano.co/) minifies our CSS.

### KSS styleguide

Components and layouts are documented in [SUMO Styleguide](https://mozilla.github.io/kitsune/_kss/) using `kss-node`
automation to generate the documentation from SCSS sources.

### Theming

Colors reach components through tokens,
so a theme is a set of token values rather than a second copy of the stylesheets.
There is a light theme, which is the default,
and a dark theme.

#### Token layers

* **Palette**, in `kitsune/sumo/static/sumo/scss/config/_color-swatches.scss`.
Named ramps such as `--color-blue-06` and `--color-graphite-03`,
emitted on `:root` and documented in the KSS styleguide.
The palette is the same in both themes.
* **Semantic tokens**, in `config/themes/_light.scss` and `config/themes/_dark.scss`.
Each file is one Sass map from token name to value.
`scss/_theme.scss` emits the light map on `:root` and the dark map on `[data-theme="dark"]`.
Tokens say what a color is for (`--color-text`, `--page-bg`, `--color-border`),
and cover surfaces, text, links, accent fills, borders, form fields, status colors, elevation shadows, and media filters.
* **Component tokens**, in the same two maps.
A component that has to vary on its own gets its own token (`--status-info-bg`, `--field-border-color-hover`),
defined in terms of semantic tokens or palette entries.

Components read tokens with `var()`.
Values that don't change with the theme,
such as fonts, spacing, and the `--radius-*` scale,
are declared once on `:root` in `_theme.scss`.

#### Rules

1. **Components never know which theme is active.**
Component SCSS reads tokens.
It never uses `[data-theme]` selectors,
hex or named colors,
`rgb()` or `hsl()`,
raw palette variables such as `var(--color-blue-06)`,
or Sass palette access such as `color('blue', '06')` and `p.$color-white`.
Anything that differs between themes is a token,
including gradients, shadows, and filters.
2. **Every token has a light and a dark value.**
A token goes in both maps,
and the build fails with an `@error` listing the missing keys if the two maps differ.
3. **Moving a component onto tokens leaves its light rendering unchanged.**
A token's light value is the value the component has now.
When a semantic token would change how a component looks in light,
give the component its own token whose light value is the component's current value.
Only a deliberate design change may alter light.

#### Dark-only overrides

Sometimes a component needs a dark value but must keep its current light value,
which may be specific to that component.
Set the token to `initial` in the light map,
the guaranteed-invalid value,
and give it the dark value in the dark map.
The component reads `var(--token, <current value>)`.
In light the fallback applies,
in dark the token does,
and both maps still have the same keys.

```scss
// config/themes/_light.scss
'promo-wash': initial,

// config/themes/_dark.scss
'promo-wash': var(--color-graphite-04),

// a component
.promo {
  background: var(--promo-wash, var(--color-callout-bg));
}
```

The fallback must be another token (a nested `var()`),
one of the allowed keywords (`transparent`, `currentColor`, `none`, `inherit`, `initial`, `unset`, `revert`, `auto`, `normal`),
or a number, percentage, or length.
Never use a raw color.
Stylelint enforces this.

#### Adding a token

1. Add the token to both `config/themes/_light.scss` and `config/themes/_dark.scss`.
The light value is the component's current value.
Reference palette entries with `var(--color-<ramp>-NN)`,
and use a raw value only when there is no palette entry or you need alpha.
2. For a color, add an entry to the matching KSS block at the top of `_light.scss`.
The swatch shows the light value and the description gives the dark value.
When you change a token's value, update its entry too.
3. Run `npm run theme:test`,
then `npm run webpack:build` and `npm run theme:contrast`.
CI runs the theme tests;
the contrast check needs a build, so run it yourself.
4. If the token is text, an icon, or a control border that sits on a token background,
add a contrast pair for it (see below).
5. If the token is decorative (a gradient, shadow, or layer), add it as `none` to `config/themes/_forced-colors.scss`.

#### Stylelint guard

`npm run stylelint` and the pre-commit stylelint hook enforce Rule 1 at error severity.
They cover all SCSS under `kitsune/sumo/static/sumo/scss` and the `<style>` blocks of the Svelte app.
Outside `config/`, they reject:

* hex colors, named colors, and color functions (`rgb()`, `rgba()`, `hsl()`, `hsla()`, `hwb()`, `lab()`, `lch()`, `oklab()`, `oklch()`, `color()`, `color-mix()`, `light-dark()`)
* raw palette properties: `var(--color-blue-06)` and the other ramp steps, plus `--color-white`, `--color-black`, and `--color-lavender`
* Sass palette access: `c.color()`, `$color-*` with or without a namespace (such as `p.$color-white`), and the `$colors` map (such as `map.get(c.$colors, 'blue')`)
* Protocol's other color-bearing Sass variables, with or without a namespace: `$link-color*`, `$background-color*`, `$body-text-color*`, `$title-text-color*`, `$field-border*` (but not `$field-border-radius`), `$select-bg*`, `$box-shadow-*`, and `$button-border-color-focus*`
* `[data-theme]` selectors
* `var()` fallbacks that aren't a token, one of the allowed keywords (listed under Dark-only overrides), or a number, percentage, or length

`config/` is exempt,
because the palette, the theme maps, and the Protocol bridge hold raw values by definition.
`scss/_theme.scss` is the only other file that may use `[data-theme]`,
because it emits the dark theme.

Files listed in the exemptions `overrides` block of `.stylelintrc`
are not checked for colors, palette access, or fallbacks.
The `[data-theme]` ban applies to them too.

`.stylelintrc` is written as JSON,
so the patterns are explained here:

* `function-disallowed-list`: `/^(rgba?|hsla?|hwb|lab|lch|oklab|oklch|color|color-mix|light-dark)$/i` matches a function name that is exactly one of the color functions.
* `declaration-property-value-disallowed-list` applies these patterns to the value of every property:
  * `var\(\s*--color-(?:[a-z-]+-\d+|white|black|lavender)(?![\w-])` matches a `var()` of a palette property, meaning a ramp step ending in digits or one of the three single-value colors.
  The lookahead keeps it from matching a longer token name that merely starts the same way.
  It rejects any `var(--color-<word>-<digits>)`, so don't name a semantic token that way.
  Adding a single-value palette entry, like `white`, `black`, or `lavender`, means adding its name to this pattern in `.stylelintrc`.
  * `\w\.color\(` matches a call to the Sass palette function through a module namespace, such as `c.color(`.
  * `\$color-` matches a Sass variable named `$color-<name>`, with or without a module namespace, such as Protocol's `p.$color-white`.
  * `\$colors(?![\w-])` matches the `$colors` map as a whole word, so `map.get(c.$colors, 'blue')` is caught but a longer name such as `$colors-foo` is not.
  * `\$(?:link-color|background-color|body-text-color|title-text-color|field-border(?!-radius)|select-bg|box-shadow-|button-border-color-focus)` matches Protocol's color-bearing Sass variables by prefix, with or without a module namespace.
  The `(?!-radius)` lookahead lets `$field-border-radius` through, because it isn't a color.
  * `var\(\s*[^,)]*,\s*(?!\s|var\(|(?:transparent|currentcolor|none|inherit|initial|unset|revert|auto|normal|-?[\d.]+(?:%|[a-z]+)?)\s*\))` matches a `var()` with a fallback, unless the fallback starts with another `var(` or is exactly one of the allowed keywords, a number, a percentage, or a length.
* `selector-disallowed-list`: `/\[\s*data-theme/i` matches any attribute selector on `data-theme`.

The guard reads declaration values and selectors.
It deliberately does not read at-rule parameters,
and it can't see inside strings,
so some things get through.
Reviewers should watch for these:

* color values in at-rule parameters: `@include foo(#fff)`, `@return #fff`, and mixin parameter defaults such as `@mixin foo($color: #fff)`
* selectors in at-rule parameters, such as `@at-root [data-theme="dark"] &`
* named colors inside Sass lists, such as `$palette: (red, blue)`
* hex colors inside SVG data URIs
* Protocol color variables not named above, such as `$field-focus-ring*`, `$choice-fill`, `$form-*`, `$gradient-*`, and `$svg-*`

#### Contrast check

`npm run theme:contrast` reads the compiled `dist/screen*.css`,
so run `npm run webpack:build` first.
It resolves the custom properties for `:root` and for `[data-theme="dark"]`,
and checks the foreground and background pairs listed in `scripts/theme/contrast-pairs.json`.

Each pair names an `fg` token, a `bg` token, the minimum ratio, and the themes to check:

```json
{ "fg": "--status-info-text", "bg": "--status-info-bg", "backdrop": "--page-bg", "min": 4.5, "themes": ["light", "dark"] }
```

Token names include the leading `--`.
`min` is `4.5` for normal text and `3` for large text and UI components.
`backdrop` is only needed when the background is translucent,
and names the surface it sits on.
`themes` lists `"light"`, `"dark"`, or both.
A token whose light value is `initial`, as in the dark-only override pattern, can only be used in a pair with `"themes": ["dark"]`,
because the checker reports "no value" for it in light.
The script exits non-zero if any pair fails.

A pair that already fails in light can be listed under `exceptions`:

* An exception covers light only.
* Each one needs a `reason`.
* It must match a declared pair.
* An exception for a pair that now passes is stale, and stale exceptions fail the check, so remove them.

Dark failures can't be excepted.
Fix the dark token instead.

#### Protocol bridge

Protocol's own components read custom properties such as `--background-color`, `--body-text-color`, and `--link-color`.
`config/_protocol-bridge.scss` points each property it lists at a theme token,
so those components follow the active theme.
Some properties point at semantic tokens (`--background-color` at `--page-bg`, `--link-color` at `--color-link`).
The rest point at `protocol-*` tokens defined in the theme maps.
In light, every `protocol-*` token holds Protocol's own value.
In dark, some point at SUMO tokens (the tertiary background and visited links, for example),
and the others keep Protocol's inverse values.
`config/themes/_dark.scss` has the current mapping.
`_theme.scss` emits the bridge after the theme blocks.

To map another Protocol property,
add it to `$mappings` in the bridge file,
with the name of a token.
The build fails if the token doesn't exist.
Protocol styles that bake in a Sass color at compile time can't be reached through custom properties.
They need component-level overrides in the bridge file.

#### Forced colors

`scss/_forced-colors.scss` makes keyboard focus visible when the browser forces its own colors.
Forced-colors mode removes box shadows,
and fields and buttons draw focus with `--focus-shadow` alone.
Under `@media (forced-colors: active)` the layer gives `:focus-visible` a 2px `Highlight` outline,
keeps a visible border on fields,
and marks selected states (checked controls, active tabs, the current page) with system colors.

It is loaded last in `screen.scss`,
so it wins over every earlier rule at equal specificity.
The existing rules that remove outlines and make field borders transparent are more specific,
so the layer uses `!important`.
This is the one place theming code uses it,
and it only applies in forced-colors mode.

#### Print

Printing always uses the light theme.
`_theme.scss` re-emits the light map for `[data-theme="dark"]` inside `@media print`,
along with `color-scheme: light`,
so a page printed from the dark theme comes out as light.
Because the whole map is re-emitted,
new tokens are covered without extra work.

#### Runtime and the flag

The `dark-mode` waffle flag turns the runtime on or off; templates read it as `DARK_MODE`.
With it off, pages render exactly as they do without the feature.
Anonymous HTML is cached and shared,
so for anonymous traffic the flag must be on or off for everyone: no percentage rollout and no testing mode.

#### Attributes

On `<html>`:

* `data-theme`: the resolved theme, `light` or `dark`. CSS reads only this one.
* `data-theme-preference`: `system`, `light`, or `dark`.
* `data-theme-owner`: an opaque per-account key. Its presence marks a logged-in page.
* `data-theme-endpoint`: the URL that saves the preference.

The server renders the last three for logged-in users only.
The head script sets the first two, and the runtime keeps them current.

#### Head script

`kitsune/sumo/theme_head.js` is inlined first in `<head>`, so the theme is set before the first paint.
It reads `data-theme-preference` on a logged-in page and `localStorage` otherwise,
treats unknown values as `system`, resolves `system` with `prefers-color-scheme`,
and sets the two attributes and `<meta name="theme-color">`
(with the flag on, the `favicon()` macro leaves out its own).
It isn't transpiled: keep it ES5, under 1 KB, and free of listeners and requests.
Don't add `<meta name="color-scheme">`: it would darken the canvas before the theme is known.

`settings.py` holds the file as `HEAD_SCRIPT` and its hash as `HEAD_SCRIPT_CSP_SOURCE`, which `script-src` allows outside `DEBUG`.
`theme_head_script()` inlines the text verbatim, so it always matches the hash.
The wiki's `doc_page_cache` keys include the hash, so editing the script never serves stale cached pages.

#### Runtime API and event

`sumo/js/theme.js`, in the common bundle:

* `getPreference()`: `system`, `light`, or `dark`.
* `getTheme()`: `light` or `dark`.
* `isActive()`: `false` where the head script didn't run; the runtime then does nothing.
* `setPreference(preference)`: applies and saves a preference, ignoring unknown values.

While the preference is `system`, the theme follows the OS.
`sumo:themechange` fires on `document` with `detail: { theme, preference }` when either changes,
so it also fires when only the preference does, as for System to Dark on a dark OS:

```js
document.addEventListener("sumo:themechange", ({ detail }) => redraw(detail.theme));
```

#### Storage and sync

* **Anonymous:** `localStorage["sumo-theme-preference"]`; other tabs follow through `storage` events.
* **Logged-in:** the `theme_preference` `Setting` row (`get_theme_preference` and `set_theme_preference` in `kitsune/users/theme.py`), rendered on every page.
Other tabs follow through `BroadcastChannel("sumo-theme")` messages `{ owner, preference }`,
ignoring other owners and never saving or re-posting what they receive.
* **Saving:** `savePreference()` in `theme-persistence.js` posts `preference` and `owner` to `POST /<locale>/users/theme` with `keepalive`.
A page keeps one save in flight, sends only the latest choice next, and doesn't retry a failed save.
* **Endpoint:** requires login and CSRF. It returns 200 with the stored preference, 400 for an unknown preference or no owner,
409 when `owner` isn't the signed-in account's key (the page then stops saving), and 404 with the flag off.

#### Switcher

`theme_switcher(id_prefix, variant, field_name=None, checked=None)` in `common_macros.html` renders the System, Light, and Dark radios
for the `themeSwitcher` Alpine component in `theme-switcher.js`:

* `id_prefix` prefixes the radio ids and names the group, so it must be unique on the page.
* `variant` adds `is-footer`, `is-menu`, or `is-field`.
* `field_name` makes it a form field that works without JavaScript; without it, the switcher renders `hidden` and appears once the runtime is active.
* `checked` is the server-rendered choice.

With the flag on, it appears in the footer, in the avatar menu, and in account settings as the `theme_preference` field of `SettingsForm`.

## Images

Images directly imported in JS files,
or referenced in CSS files,
are copied by Webpack into the build directory,
after renaming and optimizing them.

### In Django

Aside from managing images directly imported in JS and CSS files,
we also make use of Webpack to manage images used in Django itself,
in Jinja2 templates and Python code.

To do this,
we make use of the [CopyWebpackPlugin](https://webpack.js.org/plugins/copy-webpack-plugin/) to copy images under certain paths into the build directory,
after processing them through the asset pipeline.

We then hook into the Webpack build process,
in `webpack/asset-json-plugin.js`,
to generate an original to build path mapping in the `dist/source-to-asset.json` file.
We shorten the original path as explained below.

Included images are those:

* under the Protocol icons directory: `node_modules/@mozilla-protocol/core/protocol/img/icons/`,
shortened to `protocol/img/icons/`
* under the static image directory for any Django app: `kitsune/*/static/**/img/`,
shortened to `**/img/`

In Django,
the `webpack_static` helper loads the mapping,
and is used to get an output path for any image needed from those directories.

### Optimization

In the Webpack pipeline,
PNGs are run through optipng,
and SVGs are run through svgo.
