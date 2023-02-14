const pathRemovals = [
  /^node_modules\/@mozilla-protocol\/core\//,
  /^kitsune\/[^/]+\/static\//,
];

const path = require("node:path");
const root = path.resolve(__dirname, "..");

class AssetJsonPlugin {
  apply(compiler) {
    const RawSource = compiler.webpack.sources.RawSource;
    compiler.hooks.thisCompilation.tap("asset-json-plugin", (compilation) => {
      compilation.hooks.afterProcessAssets.tap("asset-json-plugin", () => {
        const sourceToAsset = {};
        for (const [k, v] of compilation.assetsInfo) {
          const source = v.sourceFilename;
          if (source) {
            // The "source" can sometimes be an absolute path, so let's ensure
            // that we're always working with a path relative to the project root.
            const relativeSource = path.relative(root, path.resolve(root, source))
            const shortSource = pathRemovals.reduce(
              (accumulator, current) => accumulator.replace(current, ""),
              relativeSource
            );
            sourceToAsset[shortSource] = k;
          }
        }
        compilation.emitAsset(
          "source-to-asset.json",
          new RawSource(JSON.stringify(sourceToAsset))
        );
      });
    });
  }
}

module.exports = AssetJsonPlugin;
