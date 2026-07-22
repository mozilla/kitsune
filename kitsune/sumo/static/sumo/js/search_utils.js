import CachedXHR from "sumo/js/cached_xhr";

var cxhr = new CachedXHR();

export default function Search(baseUrl, params) {
  this.baseUrl = baseUrl;
  this.params = Object.assign({}, params);
}

Search.prototype._buildQueryUrl = function(query, params) {
  var url = this.baseUrl + '?q=' + query;
  if (params) {
    url += '&' + params;
  }
  return url;
};

Search.prototype.setParam = function(key, value) {
  this.params[key] = value;
  return this;
};

Search.prototype.setParams = function(params) {
  Object.assign(this.params, params);
  return this;
};

Search.prototype.getParam = function(key) {
  return this.params[key];
};

Search.prototype.unsetParam = function(key) {
  delete this.params[key];
  return this;
};

Search.prototype.clearLastQuery = function() {
  this.lastQuery = '';
  this.lastParams = '';
};

Search.prototype.hasLastQuery = function() {
  return !!this.lastQuery;
};

Search.prototype.lastQueryUrl = function() {
  return this._buildQueryUrl(this.lastQuery, this.lastParams);
};

Search.prototype.queryUrl = function() {
  return this._buildQueryUrl(this.lastQuery, this.serializeParams());
};

Search.prototype.serializeParams = function(extra) {
  var params = Object.assign({}, this.params, extra);
  var paramStrings = [];
  Object.keys(params).forEach(function(key) {
    paramStrings.push(key + '=' + params[key]);
  });
  return paramStrings.join('&');
};

Search.prototype.query = function(string, callback) {
  string ||= this.lastQuery;
  var data = Object.assign({}, this.params, {q: string});

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
