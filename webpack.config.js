const path = require("path");

const entrypoints = require("./webpack/entrypoints");
const entrypointsHtml = require("./webpack/entrypoints-html");
const globalExposeRules = require("./webpack/global-expose-rules");

module.exports = (env, argv) => {
  const config = {
    resolve: {
      alias: {
        protocol: "@mozilla-protocol/core/protocol",
        sumo: path.resolve(__dirname, "kitsune/sumo/static/sumo"),
        community: path.resolve(
          __dirname,
          "kitsune/community/static/community"
        ),
        kpi: path.resolve(__dirname, "kitsune/kpi/static/kpi"),
      },
    },
    module: {
      rules: [
        {
          test: /\.es6$/,
          exclude: /node_modules/,
          use: {
            loader: "babel-loader",
          },
        },
        ...globalExposeRules,
      ],
    },
    entry: entrypoints,
    plugins: [
      ...entrypointsHtml,
    ],
    output: {
      filename:
        argv.mode === "development" ? "[name].js" : "[name].[contenthash].js",
    },
  };

  return config;
};
