const fs = require("fs");

function rerequire(path) {
  delete require.cache[path];
  return require(path);
}

class SveltePreRenderPlugin {
  constructor(options = {}) {
    this.options = options;
  }

  apply(compiler) {
    const locales = fs.readdirSync("jsi18n/jsi18n");

    compiler.hooks.assetEmitted.tap(
      "svelte-pre-render-plugin",
      (file, { outputPath, targetPath }) => {
        const routes = this.options[file];
        if (routes) {
          const Component = rerequire(targetPath).default;

          for (const locale of locales) {
            const jsi18n = rerequire(`../jsi18n/jsi18n/${locale}/djangojs.js`);
            Object.assign(global, jsi18n);

            for (const route of routes) {
              const { head = "", html } = Component.render({
                url: `/${locale}${route}`,
                locale,
              });

              fs.mkdirSync(
                `${outputPath}/${locale}${route
                  .split("/")
                  .slice(0, -1)
                  .join("/")}`,
                {
                  recursive: true,
                }
              );

              fs.writeFileSync(
                `${outputPath}/${locale}${route}.head.html`,
                head
              );
              fs.writeFileSync(
                `${outputPath}/${locale}${route}.html`,
                html
              );
            }
          }
        }
      }
    );
  }
}

module.exports = SveltePreRenderPlugin;
