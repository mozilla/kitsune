const HtmlWebpackPlugin = require("html-webpack-plugin");

const entrypoints = require("./entrypoints");

module.exports = Object.keys(entrypoints).map(entry =>
  new HtmlWebpackPlugin({
    filename: `entrypoints/${entry}.html`,
    publicPath: process.env.STATIC_URL || "/static/",
    chunks: [entry],
    inject: false,
    scriptLoading: "defer",
    templateContent: ({htmlWebpackPlugin}) => htmlWebpackPlugin.tags.headTags.join("")
  }),
);
