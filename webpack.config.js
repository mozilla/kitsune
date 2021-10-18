const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CopyPlugin = require("copy-webpack-plugin");
const ImageMinimizerPlugin = require("image-minimizer-webpack-plugin");
const AssetJsonPlugin = require("./webpack/asset-json-plugin");

const entrypoints = require("./webpack/entrypoints");
const entrypointsHtml = require("./webpack/entrypoints-html");
const globalExposeRules = require("./webpack/global-expose-rules");

const assetModuleFilename = "[name].[contenthash][ext]";

module.exports = (env, argv) => {
  const dev = argv.mode === "development";
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
        ...globalExposeRules,
      ],
    },
    entry: entrypoints,
    plugins: [
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
  };

  if (dev) {
    // eval source maps don't work with our css loaders
    config.devtool = "cheap-module-source-map";
  }

  return config;
};
