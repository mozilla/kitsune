const path = require("path");
const nunjucks = require("nunjucks");

// To keep things simpler here, we don't attempt to resolve template dependencies.
// So, you must manually import all dependant templates.

module.exports = function (source) {
  return nunjucks.precompileString(source, {
    name: path.parse(this.resourcePath).base,
  });
};
