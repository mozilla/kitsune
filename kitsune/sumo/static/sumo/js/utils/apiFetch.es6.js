/* globals k:false */
import 'fetch'; // polyfill

export default function apiFetch(url, options) {
  if ('data' in options) {
    if ('body' in options) {
      throw new Error('Only pass one of `options.data` and `options.body`.');
    }
    let method = (options.method || 'get').toLowerCase();
    if (method === 'get' || method === 'head') {
      if (url.indexOf('?') === -1) {
        url += '?';
      } else {
        url += '&';
      }
      /* The slice is to remove the ? that that
       * `queryParamStringFromDict` includes, since it was added above. */
      url += k.queryParamStringFromDict(options.data).slice(1);
    } else {
      options.body = JSON.stringify(options.data);
    }
    delete options.data;
  }

  if (!('headers' in options)) {
    options.headers = {};
  }
  options.headers['Content-Type'] = 'application/json';

  return fetch(url, options)
  .then(res => {
    if (res.status >= 400) {
      throw new Error(res.statusText);
    } else {
      return res.json();
    }
  });
}
