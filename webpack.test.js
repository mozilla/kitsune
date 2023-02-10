const { merge } = require("webpack-merge");
const glob = require("glob");

const common = require("./webpack.common.js");

module.exports = merge(common, {
  target: "node",
  entry: {
    tests: [...glob.sync("./kitsune/*/static/*/js/tests/*.js")],
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
    ],
  },
});
