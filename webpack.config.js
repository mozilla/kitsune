const webpack = require("webpack");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CopyPlugin = require("copy-webpack-plugin");
const ImageMinimizerPlugin = require("image-minimizer-webpack-plugin");
const AssetJsonPlugin = require("./webpack/asset-json-plugin");

const aliases = require("./webpack/aliases");
const entrypoints = require("./webpack/entrypoints");
const entrypointsHtml = require("./webpack/entrypoints-html");
const exportRules = require("./webpack/export-rules");

const assetModuleFilename = "[name].[contenthash][ext]";

module.exports = (env, argv) => {
  const dev = argv.mode === "development";
  const config = {
    resolve: {
      alias: aliases,
    },
    module: {
      rules: [
        {
          test: /\.js$/,
          exclude: /node_modules/,
          use: {
            loader: "babel-loader",
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
        ...exportRules,
      ],
    },
    entry: entrypoints,
    plugins: [
      new webpack.ProvidePlugin({
        $: "jquery",
        jQuery: "jquery",
        "window.jQuery": "jquery",
      }),
      new MiniCssExtractPlugin({
        filename: dev ? "[name].css" : "[name].[contenthash].css",
      }),
      ...entrypointsHtml,
      new CopyPlugin({
        patterns: [
          { from: "node_modules/@mozilla-protocol/core/protocol/img/icons/**", to: assetModuleFilename },
          { from: "kitsune/*/static/**/img/**", to: assetModuleFilename },
        ],
      }),
      new ImageMinimizerPlugin({
        minimizerOptions: {
          plugins: [
            "optipng",
            "svgo",
          ]
        }
      }),
      new AssetJsonPlugin(),
    ],
    output: {
      filename: dev ? "[name].js" : "[name].[contenthash].js",
      assetModuleFilename: assetModuleFilename,
    },
    cache: dev ? { type: "filesystem" } : false,
    optimization: {
      splitChunks: {
        chunks: 'all',
      },
    },
  };

  if (dev) {
    // eval source maps don't work with our css loaders
    config.devtool = "cheap-module-source-map";
  }

  return config;
};
