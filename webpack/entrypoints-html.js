const HtmlWebpackPlugin = require("html-webpack-plugin");

const entrypoints = require("./entrypoints");

module.exports = Object.keys(entrypoints).map(entry =>
  new HtmlWebpackPlugin({
    filename: `entrypoints/${entry}.html`,
    // use a jinja tag so the static url can be resolved at runtime:
    publicPath: "{{ STATIC_URL_WEBPACK }}",
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
