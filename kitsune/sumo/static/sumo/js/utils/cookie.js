/*
 * Cookie helpers - vanilla replacement for the vendored jquery.cookie plugin.
 */

// Read a cookie by name. Returns undefined when the cookie is not set,
// mirroring $.cookie(name).
export function getCookie(name) {
  const cookies = document.cookie ? document.cookie.split("; ") : [];
  for (const cookie of cookies) {
    const eq = cookie.indexOf("=");
    const key = decodeURIComponent(eq > -1 ? cookie.slice(0, eq) : cookie);
    if (key === name) {
      return decodeURIComponent(eq > -1 ? cookie.slice(eq + 1) : "");
    }
  }
  return undefined;
}

// Write a cookie. Options mirror the subset of jquery.cookie we actually use:
//   expires - number of days (or a Date) until the cookie expires
//   path    - defaults to "/"
//   domain, secure
export function setCookie(name, value, options = {}) {
  let cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}`;

  let { expires } = options;
  if (typeof expires === "number") {
    const days = expires;
    expires = new Date();
    expires.setDate(expires.getDate() + days);
  }
  if (expires instanceof Date) {
    cookie += `; expires=${expires.toUTCString()}`;
  }

  cookie += `; path=${options.path || "/"}`;
  if (options.domain) {
    cookie += `; domain=${options.domain}`;
  }
  if (options.secure) {
    cookie += "; secure";
  }

  document.cookie = cookie;
}

// Delete a cookie by setting it to expire in the past.
export function removeCookie(name, options = {}) {
  setCookie(name, "", { ...options, expires: -1 });
}
