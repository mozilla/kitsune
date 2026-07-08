import { apiFetch } from "sumo/js/utils/fetch";

export default function CachedXHR() {}

// Module-level cache shared across instances (matches the previous closure).
let cache = {};

CachedXHR.prototype.dumpCache = function () {
  return cache;
};

CachedXHR.prototype.clearCache = function () {
  cache = {};
  return this;
};

CachedXHR.prototype.fetch = function (url, cacheKey) {
  var key = url;
  if (cacheKey) {
    key += "::" + cacheKey;
  }
  return cache[key];
};

CachedXHR.prototype.store = function (url, cacheKey, lifetime, data) {
  var key = url;
  if (cacheKey) {
    key += "::" + cacheKey;
  }
  cache[key] = {
    expires: Date.now() + lifetime,
    data: data,
  };
  return this;
};

CachedXHR.prototype.request = function (url, options) {
  var self = this;

  options = Object.assign({ lifetime: 5 * 60 * 1000 }, options);
  var success = options.success;

  var cached = self.fetch(url, options.cacheKey);
  if (cached && cached.expires > Date.now() && !options.forceReload) {
    if (success) {
      success(cached.data);
    }
    return self;
  }

  apiFetch(url, {
    method: "GET",
    data: options.data,
    dataType: options.dataType || "json",
  })
    .then(function (data) {
      self.store(url, options.cacheKey, options.lifetime, data);
      if (success) {
        success(data);
      }
    })
    .catch(function (error) {
      if (options.error) {
        options.error(error);
      }
    });

  return self;
};
