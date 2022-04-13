# Svelte

## CSS/SASS

Svelte supports writing CSS directly in a component within `<style>` tags,
as well as writing compiled-to-CSS languages like SASS within `<style lang="scss">` tags.

CSS written this way is automatically scoped to the component:
[read more in the Svelte docs](https://svelte.dev/docs#component-format-style).

This SASS to CSS compilation is handled by `svelte-preprocess`,
and the resulting CSS is handed to Wepback for further processing.
Since Webpack isn't involved in SASS compilation within Svelte components,
care must be taken in a few areas:

1. Because Webpack isn't handling `@use` and `@import` resolution,
   it's not possible to use its aliases to reference paths to other SASS files.
   Instead paths relative to the Svelte component,
   or full node module paths,
   must be used.
   This _doesn't_ include paths not processed by the SASS compiler,
   such as paths to images in `url()` functions,
   as these are still handled by Webpack.
   To illustrate:

```scss
@use "@mozilla-protocol/core/protocol/css/includes/lib" as p;
@use "../../kitsune/sumo/static/sumo/scss/config/typography-mixins";
// ^ here we must use a full or relative path, as svelte-preprocess is resolving this

div {
    background: url("protocol/img/icons/reader-mode.svg");
    // ^ here we can use a webpack alias, as webpack is resolving this
    background-size: p.$spacing-md;
    @include typography-mixins.text-display-sm;
}
```

2. As a knock-on effect of the above,
   any partials used in both our main CSS bundle,
   as well as a Svelte component (like the `typography-mixins` above)
   must not use Webpack aliases in their own imports,
   otherwise `svelte-preprocess` won't be able to resolve them.

3. Partials should be careful to not accidentally include or import CSS blocks outside of mixin defintions.
   This is because neither `svelte-preprocess` nor the Webpack `sass-loader` are able to chunk split `@import`s and `@use`s,
   or even de-duplicate their use across Svelte components (due to the scoped nature of the CSS within).
   Not doing this will lead to unnecessarily duplicated code.

## Pre-rendering

To pre-render Svelte components a two-step process is required.

First the components must pass through the Svelte compiler,
with the appropriate flags enabled to compile components for server-side rendering (SSR).
Then those compiled components must be rendered into static HTML.
We do both these steps in Webpack using the `webpack.pre-render.js` config file.

In order to pre-render a route,
add it to the config object passed to `svelte-pre-render-plugin` in `webpack.pre-render.js`,
referencing the entrypoint containing the component you want to render:

```
entry: {
    foobar: "./svelte/SomeComponent",
    barfoo: "./svelte/AnotherComponent",
},
plugins: [
    new SveltePreRenderPlugin({
        "foobar.js": [
            "/route-1",
            "/route-2",
            "/route-2/subroute",
        ],
        "barfoo.js": [
            "/route-3",
        ],
    }),
],
```
