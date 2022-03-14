const fs = require("fs");
const path = require("path");

module.exports = function (source) {
  const assetMap = JSON.parse(
    fs.readFileSync(
      path.join(__dirname, "../dist/source-to-asset.json"),
      "utf-8"
    )
  );
  return (
    "{{ STATIC_URL_WEBPACK }}/" +
      assetMap[this.resourcePath.replace(path.join(__dirname, "../"), "")] || ""
  );
};
