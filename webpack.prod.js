const { mergeWithCustomize, unique } = require("webpack-merge");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

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
  ],
  cache: false,
  devtool: false,
  output: {
    filename: "[name].[contenthash].js",
  },
});
