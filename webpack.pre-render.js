const path = require("path");
const sveltePreprocess = require("svelte-preprocess");
const SveltePreRenderPlugin = require("./webpack/svelte-pre-render-plugin");

module.exports = {
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
      ]
    })
  ],
  mode: "production",
  resolve: {
    alias: {
      svelte: path.resolve("node_modules", "svelte"),
    },
    extensions: [".mjs", ".js", ".svelte"],
    mainFields: ["svelte", "browser", "module", "main"],
  },
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
        // required to prevent errors from Svelte on Webpack 5+, omit on Webpack 4
        test: /node_modules\/svelte\/.*\.mjs$/,
        resolve: {
          fullySpecified: false,
        },
      },
    ],
  },
  devtool: "cheap-module-source-map",
  output: {
    filename: "[name].js",
    path: path.resolve(__dirname, "dist/pre-render"),
    library: {
      type: "commonjs",
    },
  },
  target: "node",
};
