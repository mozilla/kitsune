/*
 * apiFetch - a small fetch() wrapper that replaces $.ajax and the global
 * $.ajaxSetup CSRF hook (main.js). It:
 *   - attaches the X-CSRFToken header on unsafe methods (reading the token the
 *     same way the old $.ajaxSetup did: csrftoken cookie, then a
 *     csrfmiddlewaretoken input on the page),
 *   - sends the X-Requested-With header jQuery added by default,
 *   - serializes a `data` object as a query string (GET/HEAD) or a
 *     form-urlencoded body (otherwise); FormData is passed through untouched,
 *   - parses the response as JSON, HTML, or text and throws on non-2xx.
 */

import { getCookie } from "sumo/js/utils/cookie";

const SAFE_METHOD = /^(GET|HEAD|OPTIONS|TRACE)$/i;

export function getCsrfToken() {
  let token = getCookie("csrftoken");
  if (!token) {
    const input = document.querySelector("input[name=csrfmiddlewaretoken]");
    if (input) {
      token = input.value;
    }
  }
  return token;
}

function encodeParams(data) {
  const params = new URLSearchParams();
  for (const key of Object.keys(data)) {
    const value = data[key];
    if (value === undefined || value === null) {
      continue;
    }
    if (Array.isArray(value)) {
      for (const item of value) {
        params.append(key, item);
      }
    } else {
      params.append(key, value);
    }
  }
  return params;
}

// Parse JSON via text() so an empty body resolves to null - matching jQuery's
// $.ajax, which tolerated an empty response for dataType "json" instead of
// throwing the way response.json() does.
async function parseJson(response) {
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

async function parseBody(response, dataType) {
  if (dataType === "json") {
    return parseJson(response);
  }
  if (dataType === "html" || dataType === "text") {
    return response.text();
  }
  const contentType = response.headers.get("Content-Type") || "";
  if (contentType.includes("application/json")) {
    return parseJson(response);
  }
  return response.text();
}

export async function apiFetch(url, options = {}) {
  const { method = "GET", data, dataType, headers = {}, ...rest } = options;

  const requestHeaders = { "X-Requested-With": "XMLHttpRequest", ...headers };
  const init = {
    method,
    headers: requestHeaders,
    credentials: "same-origin",
    ...rest,
  };

  if (!SAFE_METHOD.test(method)) {
    const token = getCsrfToken();
    if (token) {
      requestHeaders["X-CSRFToken"] = token;
    }
  }

  let requestUrl = url;
  if (data !== undefined && data !== null) {
    if (SAFE_METHOD.test(method)) {
      const query = encodeParams(data).toString();
      if (query) {
        requestUrl += (url.includes("?") ? "&" : "?") + query;
      }
    } else if (data instanceof FormData) {
      init.body = data;
    } else {
      requestHeaders["Content-Type"] =
        "application/x-www-form-urlencoded; charset=UTF-8";
      init.body = encodeParams(data).toString();
    }
  }

  const response = await window.fetch(requestUrl, init);

  if (!response.ok) {
    const error = new Error(`Request to ${url} failed (${response.status})`);
    error.response = response;
    // Attach the parsed body when we can, but never let an unparseable body
    // (e.g. an HTML error page for a dataType:"json" request) throw here and
    // mask the real HTTP status.
    try {
      error.body = await parseBody(response, dataType);
    } catch {
      error.body = null;
    }
    throw error;
  }

  return await parseBody(response, dataType);
}
