(function($, _) {
  window.k = k || {};

  var cxhr = new k.CachedXHR();

  function Search(baseUrl, params) {
    this.baseUrl = baseUrl;
    this.params = $.extend({}, params);
  };

  Search.prototype.setParam = function(key, value) {
    this.params[key] = value;
    return this;
  };

  Search.prototype.setParams = function(params) {
    $.extend(this.params, params);
    return this;
  };

  Search.prototype.getParam = function(key) {
    this.params[key] = value;
    return this;
  };

  Search.prototype.unsetParam = function(key) {
    delete this.params[key];
    return this;
  };

  Search.prototype.clearLastQuery = function() {
    this.lastQuery = '';
    this.lastParams = '';
  }

  Search.prototype.serializeParams= function(extra) {
    var params = $.extend({}, this.params, extra);
    var keys = Object.keys(params);
    var paramStrings = [];
    $(keys).each(function() {
      paramStrings.push(this + '=' + params[this]);
    });
    return paramStrings.join('&');
  };

  Search.prototype.query = function(string, callback) {
    var data = $.extend({}, this.params, {q: string});

    this.lastQuery = string;
    this.lastParams = this.serializeParams({q: string});

    cxhr.request(this.baseUrl, {
      cacheKey: this.lastParams,
      data: data,
      dataType: 'json',
      success: callback
    });

    return this;
  };

  k.Search = Search;
})(jQuery, k.nunjucksEnv);
