import path from 'path';
import {rerequire} from 'mocha-jsdom';
import {FileSystemLoader} from 'nunjucks';

/**
 * Load and set up nunjucks and the Sumo nunjucks environment for Mocha tests.
 */
export default function() {
  global.beforeEach(() => {
    let nunjucks = rerequire('nunjucks');

    let originalConfigure = nunjucks.configure;
    // Monkey patch the nunjucks configure function to allow leaving off
    // the search path. This is because the tests sometimes treat Nunjucks
    // as if it is running in a Node environement, and other times like
    // it is running a web environment. Those two use cases vary in
    // (among other things) if they use a load path or not.
    nunjucks.configure = function(one, two) {
      let loaderPath, opts;
      if (typeof one === 'object' && typeof two === 'undefined') {
        loaderPath = '.';
        opts = one;
      } else if (typeof one === 'string' && typeof two === 'object') {
        loaderPath = one;
        opts = two;
      } else {
        throw new Error('Unrecognized parameters to nunjucks.configure monkeypatch.');
      }
      return originalConfigure(loaderPath, opts);
    };

    global.nunjucks = nunjucks;
    if (global.window) {
      global.window.nunjucks = nunjucks;
    }

    rerequire('../../nunjucks.js');
    global.window.k.nunjucksEnv.loaders = [new FileSystemLoader('kitsune/sumo/static/sumo/tpl')];
    global.window.k.nunjucksEnv.initCache();
  });

  global.afterEach(() => {
    delete global.nunjucks;
    if (global.window) {
      delete global.window.nunjucks;
    }
  });
}
