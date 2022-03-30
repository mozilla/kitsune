const { mergeWithRules } = require("webpack-merge");
const path = require("path");
const sveltePreprocess = require("svelte-preprocess");
const SveltePreRenderPlugin = require("./webpack/svelte-pre-render-plugin");

const common = require("./webpack.common.js");

module.exports = mergeWithRules({
  module: {
    rules: {
      test: "match",
      type: "replace",
      use: "replace",
    },
  },
})(common, {
  entry: {
    contribute: "./svelte/contribute/Contribute",
  },
  plugins: [
    new SveltePreRenderPlugin({
      "contribute.js": [
        "/contribute",
        "/contribute/forum",
        "/contribute/kb",
        "/contribute/social",
        "/contribute/l10n",
        "/contribute/play-store",
      ],
    }),
  ],
  mode: "production",
  module: {
    rules: [
      {
        test: /\.svelte$/,
        use: {
          loader: "svelte-loader",
          options: {
            emitCss: false,
            preprocess: sveltePreprocess(),
            compilerOptions: {
              generate: "ssr",
              hydratable: true,
            },
          },
        },
      },
      {
        test: /\.(svg|png|gif|woff2?)$/,
        type: "asset/source",
        use: {
          loader: path.resolve("./webpack/ssr-asset-loader"),
        },
      },
    ],
  },
  output: {
    filename: "[name].js",
    path: path.resolve(__dirname, "dist/pre-render"),
    library: {
      type: "commonjs",
    },
  },
  target: "node",
});
