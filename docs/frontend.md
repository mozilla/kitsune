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
