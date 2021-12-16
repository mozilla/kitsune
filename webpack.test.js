const { merge } = require("webpack-merge");
const glob = require("glob");

const common = require("./webpack.common.js");

module.exports = merge(common, {
  target: "node",
  entry: {
    tests: [...glob.sync("./kitsune/*/static/*/js/tests/*.js")],
  },
});
