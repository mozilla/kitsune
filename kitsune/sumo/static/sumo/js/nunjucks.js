import nunjucks from "nunjucks/browser/nunjucks-slim";

(function($) {
  window.k = window.k || {};

  var env = nunjucks.configure({autoescape: true});

  env.addGlobal('_', gettext);
  env.addGlobal('ngettext', window.ngettext);

  env.addFilter('f', function(fmt, obj, named) {
    var keys = Object.keys(obj);
    var escape = env.getFilter('escape');

    for (var i = 0; i < keys.length; i++) {
      obj[keys[i]] = escape(obj[keys[i]]);
    }

    return interpolate(fmt, obj, named);
  });

  env.addFilter('urlparams', function(url, params) {
    if (url) {
      var i;
      var base = url.split('?')[0];
      var qs = url.split('?')[1] || '';
      qs = qs.split('&');

      var old_params = {};
      for (i = 0; i < qs.length; i++) {
        var s = qs[i].split('=');
        old_params[s.shift()] = s.join('=');
      }

      params = $.extend({}, old_params, params);

      url = base;
      var keys = Object.keys(params);
      for (i = 0; i < keys.length; i++) {
        url += (url.indexOf('?') === -1) ? '?' : '&';
        url += keys[i];
        var val = params[keys[i]];
        if (val !== undefined && val !== null && val !== '') {
          url += '=' + val;
        }
      }

      return url;
    }
  });

  env.addFilter('class_selected', function(v1, v2) {
    if (v1 === v2) {
      return ' class=selected ';
    }
    return '';
  });

  env.addFilter('stringify', function(obj) {
    return JSON.stringify(obj);
  });

  env.addFilter('encodeURI', function(uri) {
    return encodeURI(uri);
  });

  k.nunjucksEnv = env;
})(jQuery);
