const webpack = require("webpack");
const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = {
  mode: "development",
  resolve: {
    alias: {
      protocol: "@mozilla-protocol/core/protocol",
      sumo: path.resolve(__dirname, "kitsune/sumo/static/sumo"),
      community: path.resolve(__dirname, "kitsune/community/static/community"),
      kpi: path.resolve(__dirname, "kitsune/kpi/static/kpi"),
    },
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
          options: {
            presets: ["@babel/preset-env"],
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
        test: /\.scss$/,
        use: [
          MiniCssExtractPlugin.loader,
          "css-loader",
          "postcss-loader",
          "sass-loader",
        ],
      },
      {
        test: /\.(svg|png|gif|woff2?)$/,
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
