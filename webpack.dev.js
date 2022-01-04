const { merge } = require("webpack-merge");
const CopyPlugin = require("copy-webpack-plugin");
const ImageMinimizerPlugin = require("image-minimizer-webpack-plugin");
const AssetJsonPlugin = require("./webpack/asset-json-plugin");

const common = require("./webpack.common.js");
const entrypoints = require("./webpack/entrypoints");
const entrypointsHtml = require("./webpack/entrypoints-html");

const assetModuleFilename = "[name].[contenthash][ext]";

module.exports = merge(common, {
  entry: entrypoints,
  plugins: [
    ...entrypointsHtml,
    new CopyPlugin({
      patterns: [
        {
          from: "node_modules/@mozilla-protocol/core/protocol/img/icons/**",
          to: assetModuleFilename,
        },
        { from: "kitsune/*/static/**/img/**", to: assetModuleFilename },
      ],
    }),
    new ImageMinimizerPlugin({
      minimizerOptions: {
        plugins: ["optipng", "svgo"],
      },
    }),
    new AssetJsonPlugin(),
  ],
  optimization: {
    splitChunks: {
      chunks: "all",
    },
  },
  output: {
    assetModuleFilename: assetModuleFilename,
  },
});
