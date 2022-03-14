const { mergeWithCustomize, unique } = require("webpack-merge");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CompressionPlugin = require("compression-webpack-plugin");
const zlib = require("zlib");

const dev = require("./webpack.dev.js");

module.exports = mergeWithCustomize({
  customizeArray: unique(
    "plugins",
    ["MiniCssExtractPlugin"],
    (plugin) => plugin.constructor && plugin.constructor.name
  ),
})(dev, {
  mode: "production",
  plugins: [
    new MiniCssExtractPlugin({
      filename: "[name].[contenthash].css",
    }),
    new CompressionPlugin({
      algorithm: "gzip",
      filename: "[path][base].gz",
      compressionOptions: {
        params: {
          level: 9,
        },
      },
      minRatio: 0.9,
    }),
    new CompressionPlugin({
      algorithm: "brotliCompress",
      filename: "[path][base].br",
      compressionOptions: {
        params: {
          [zlib.constants.BROTLI_PARAM_QUALITY]:
            zlib.constants.BROTLI_MAX_QUALITY,
        },
      },
      minRatio: 0.9,
    }),
  ],
  cache: false,
  devtool: false,
  output: {
    filename: "[name].[contenthash].js",
  },
});
