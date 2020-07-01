/* globals k:false */

export default function apiFetch(url, options = {}) {
  return apiFetchRaw(url, options).then((res) => {
    if (res.status >= 400) {
      throw new Error(res.statusText);
    } else if (res.status === 204) {
      return res;
    } else {
      return res.text().then((text) => {
        if (text === "") {
          return {};
        } else {
          return JSON.parse(text);
        }
      });
    }
  });
}

export function apiFetchRaw(url, options = {}) {
  if (url.indexOf("?") === -1) {
    url += "?format=json&";
  } else {
    url += "&format=json&";
  }

  if ("data" in options) {
    if ("body" in options) {
      throw new Error("Only pass one of `options.data` and `options.body`.");
    }
    let method = (options.method || "get").toLowerCase();
    if (method === "get" || method === "head") {
      /* The slice is to remove the ? that that
       * `queryParamStringFromDict` includes, since it was added above. */
      url += k.queryParamStringFromDict(options.data).slice(1);
    } else {
      options.body = JSON.stringify(options.data);
    }
    delete options.data;
  }

  if (!("headers" in options)) {
    options.headers = {};
  }
  options.headers["Content-Type"] = "application/json";

  return fetch(url, options);
}
