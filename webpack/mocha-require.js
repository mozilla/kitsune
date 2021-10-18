require("@babel/register")({
  plugins: [
    [
      "module-resolver",
      {
        // make babel resolve our webpack aliases in tests
        alias: require("./aliases"),
      },
    ],
  ],
});

// make images imports return null, we don't need them in tests
require.extensions[".svg"] = () => null;
require.extensions[".png"] = () => null;
