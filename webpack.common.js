const webpack = require("webpack");
const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const sveltePreprocess = require("svelte-preprocess");

module.exports = {
  mode: "development",
  resolve: {
    alias: {
      protocol: "@mozilla-protocol/core/protocol",
      sumo: path.resolve(__dirname, "kitsune/sumo/static/sumo"),
      community: path.resolve(__dirname, "kitsune/community/static/community"),
      kpi: path.resolve(__dirname, "kitsune/kpi/static/kpi"),
      svelte: path.resolve("node_modules", "svelte"),
    },
    extensions: [".mjs", ".js", ".svelte"],
    mainFields: ["svelte", "browser", "module", "main"],
  },
  module: {
    rules: [
      {
        test: /\.(js|svelte)$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
          options: {
            presets: ["@babel/preset-env"],
            plugins: [
              [
                "@babel/plugin-transform-runtime",
                {
                  version: "^7.16.7",
                },
              ],
            ],
          },
        },
      },
      {
        test: /\.njk$/,
        use: {
          loader: path.resolve("./webpack/nunjucks-loader"),
        },
      },
      {
        test: /\.svelte$/,
        use: {
          loader: "svelte-loader",
          options: {
            emitCss: true,
            preprocess: sveltePreprocess(),
            compilerOptions: {
              hydratable: true,
            },
          },
        },
      },
      {
        // required to prevent errors from Svelte on Webpack 5+
        test: /node_modules\/svelte\/.*\.mjs$/,
        resolve: {
          fullySpecified: false,
        },
      },
      {
        test: /\.s?css$/,
        exclude: /\.styles.scss$/,
        use: [
          MiniCssExtractPlugin.loader,
          "css-loader",
          "postcss-loader",
          "sass-loader",
        ],
      },
      {
        test: /\.styles.scss$/,
        exclude: /node_modules/,
        type: "asset/resource",
        use: ["sass-loader"],
        generator: {
          filename: "[name].[contenthash].css"
        }
      },
      {
        test: /\.(svg|png|webp|gif|woff2?)$/,
        type: "asset/resource",
      },
      // we copy these libraries from external sources, so define their exports here,
      // rather than having to modify them, making updating them more difficult:
      exports(
        "./kitsune/sumo/static/sumo/js/libs/dnt-helper.js",
        "default Mozilla.dntEnabled"
      ),
      exports(
        "./kitsune/sumo/static/sumo/js/libs/uitour.js",
        "default Mozilla.UITour"
      ),
    ],
  },
  plugins: [
    new webpack.ProvidePlugin({
      $: "jquery",
      jQuery: "jquery",
      "window.jQuery": "jquery",
    }),
    new MiniCssExtractPlugin({
      filename: "[name].css",
    }),
    new webpack.DefinePlugin({
      "process.env": JSON.stringify(process.env),
    }),
  ],
  cache: {
    type: "filesystem",
  },
  devtool: "cheap-module-source-map",
  output: {
    filename: "[name].js",
    // be sure to update kitsune.settings.WHITENOISE_IMMUTABLE_FILE_TEST if changing this:
    hashDigestLength: 16,
  },
};

function exports(path, exports) {
  // export the named variable
  return {
    test: require.resolve(path),
    loader: "exports-loader",
    options: {
      type: "module",
      exports,
    },
  };
}
