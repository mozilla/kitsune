module.exports = [
  // we copy these libraries from external sources, so define their exports here,
  // rather than having to modify them, making updating them more difficult:
  exports(
    "../kitsune/sumo/static/sumo/js/libs/dnt-helper.js",
    "default Mozilla.dntEnabled"
  ),
  exports(
    "../kitsune/sumo/static/sumo/js/libs/uitour.js",
    "default Mozilla.UITour"
  ),
];

function exports(path, exports) {
  // export the named variable
  return {
    test: require.resolve(path),
    loader: "exports-loader",
    options: {
      type: "module",
      exports,
    },
  };
}
