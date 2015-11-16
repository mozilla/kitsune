import path from 'path';
import {rerequire} from 'mocha-jsdom';
import {FileSystemLoader} from 'nunjucks';

/**
 * Load and set up nunjucks and the Sumo nunjucks environment for Mocha tests.
 */
export default function() {
  global.beforeEach(() => {
    let nunjucks = rerequire('nunjucks');

    global.nunjucks = nunjucks;
    if (global.window) {
      global.window.nunjucks = nunjucks;
    }

    const originalConfigure = nunjucks.configure;
    nunjucks.configure = opts => {
      opts.watch = false;
      return originalConfigure(opts);
    };

    rerequire('../../nunjucks.js');
    global.window.k.nunjucksEnv.loaders = [
      new FileSystemLoader('kitsune/sumo/static/sumo/tpl', true, true)
    ];
    global.window.k.nunjucksEnv.initCache();
  });

  global.afterEach(() => {
    delete global.nunjucks;
    delete global.nunjucksEnv;
    if (global.window) {
      delete global.window.nunjucks;
    }
  });
}
