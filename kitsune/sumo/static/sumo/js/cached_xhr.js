(function($) {
  window.k = window.k || {};

  var cache = {};

  function CachedXHR() {}

  CachedXHR.prototype.dumpCache = function() {
    return cache;
  };

  CachedXHR.prototype.clearCache = function() {
    cache = {};
    return this;
  };

  CachedXHR.prototype.fetch = function(url, cacheKey) {
    var key = url;
    if (cacheKey) {
      key += '::' + cacheKey;
    }
    return cache[key];
  };

  CachedXHR.prototype.store = function(url, cacheKey, lifetime, data, textStatus, jqXHR) {
    var key = url;
    if (cacheKey) {
      key += '::' + cacheKey;
    }
    cache[key] = {
      'expires': Date.now() + lifetime,
      'data': data,
      'textStatus': textStatus,
      'jqXHR': jqXHR
    };
    return this;
  };

  CachedXHR.prototype.request = function(url, options) {
    var self = this;

    options = $.extend({
      'lifetime': 5 * 60 * 1000
    }, options);

    var success = options.success;

    var callback = function(data, textStatus, jqXHR) {
      self.store(url, options.cacheKey, options.lifetime, data, textStatus, jqXHR);
      if (success) {
        success(data, textStatus, jqXHR);
      }
    };

    options.success = callback;

    var cached = self.fetch(url, options.cacheKey);
    if (cached && cached.expires > Date.now() && !options.forceReload) {
      if (success) {
        success(cached.data, cached.textStatus, cached.jqXHR);
      }
    } else {
      $.ajax(url, options);
    }

    return self;
  };

  k.CachedXHR = CachedXHR;
})(jQuery);
