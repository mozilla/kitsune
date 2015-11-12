/**
 * Install globals into the jsdom namespace.
 * @param  {function} mapFunc This function will be called to get the list of
 *   things to install into the namespace. Should return an object of keys
 *   to values to install.
 */
export default function(mapFunc) {
  return function(options) {
    let map;

    global.beforeEach(() => {
      map = mapFunc(options);
      for (let key in map) {
        let val = map[key];
        global[key] = val;
        if (global.window) {
          global.window[key] = val;
        }
      }
    });

    global.afterEach(() => {
      for (let key in map) {
        delete global[key];
        if (global.window) {
          delete global.window[key];
        }
      }
    });
  };
}
