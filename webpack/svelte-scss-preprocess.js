const path = require("path");
const { fileURLToPath, pathToFileURL } = require("url");
const sass = require("sass");

module.exports = {
  style({ content, attributes, filename }) {
    if (attributes.lang !== "scss" || !content) {
      return { code: content };
    }

    const result = sass.compileString(content, {
      url: pathToFileURL(filename),
      loadPaths: ["node_modules", process.cwd(), path.dirname(filename)],
      sourceMap: true,
      style: "expanded",
    });

    return {
      code: result.css,
      map: result.sourceMap,
      dependencies: result.loadedUrls
        .filter((url) => url.protocol === "file:")
        .map(fileURLToPath)
        .filter((file) => file !== filename),
    };
  },
};
