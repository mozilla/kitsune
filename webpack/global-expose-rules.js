// because most of our JS stack was written well before modules were a thing,
// many files place variables in the global scope for other files to use.
// in webpack, unless a file explicitly places a variable under `window.`,
// we have to expose each of these variables manually:
module.exports = [
  // expose these library exports globally:
  expose("nunjucks/browser/nunjucks-slim.js", "nunjucks"),
  expose("codemirror/lib/codemirror.js", "CodeMirror"),
  expose(
    "../kitsune/sumo/static/sumo/js/protocol-details-init.js",
    "detailsInit detailsInit"
  ),
  expose("../kitsune/sumo/static/sumo/js/sumo-tabs.js", "tabsInit tabsInit"),
  // wrap these files to make them behave like an es6 module, exporting the named variable, and expose that globally:
  exportAndExpose("../kitsune/sumo/static/sumo/js/analytics.js", "trackEvent"),
  exportAndExpose("../kitsune/sumo/static/sumo/js/upload.js", "dialogSet"),
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
  // this library attempts to expose a bunch of stuff globally by adding them to `this`, imports-loader makes that work:
  {
    test: require.resolve(
      "../kitsune/sumo/static/sumo/js/libs/diff_match_patch_uncompressed.js"
    ),
    loader: "imports-loader",
    options: {
      wrapper: "window",
    },
  },
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

function expose(path, exposes) {
  // expose a module's export globally
  return {
    test: require.resolve(path),
    loader: "expose-loader",
    options: {
      exposes,
    },
  };
}

function exportAndExpose(path, funcName) {
  // export a function or variable from a module, and expose it globally
  return {
    test: require.resolve(path),
    use: [
      {
        loader: "expose-loader",
        options: {
          exposes: `${funcName} default`,
        },
      },
      {
        loader: "exports-loader",
        options: {
          type: "module",
          exports: `default ${funcName}`,
        },
      },
    ],
  };
}
