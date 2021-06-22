const HtmlWebpackPlugin = require("html-webpack-plugin");

const entrypoints = require("./entrypoints");

module.exports = Object.keys(entrypoints).map(entry =>
  new HtmlWebpackPlugin({
    filename: `entrypoints/${entry}.html`,
    publicPath: process.env.STATIC_URL || "/static/",
    chunks: [entry],
    inject: false,
    scriptLoading: "defer",
    templateContent: ({htmlWebpackPlugin}) => {
      if (entry == "screen") {
        return `<link href="${htmlWebpackPlugin.files.css[0]}" rel="stylesheet">`;
      }
      return htmlWebpackPlugin.tags.headTags.join("");
    }
  }),
);
