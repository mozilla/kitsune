/* global nunjucks:false, gettext:false, ngettext:false, interpolate:false, k:false, jQuery:false */
(function($) {
  window.k = window.k || {};

  var env = nunjucks.configure({autoescape: true});

  env.addGlobal('_', gettext);
  env.addGlobal('ngettext', window.ngettext);

  // TODO: Get rid of these and replace filters with functions in templates
  env.addFilter('gettext', gettext);
  env.addFilter('ngettext', ngettext);
  env.addFilter('interpolate', function(fmt, obj, named) {
    var keys = Object.keys(obj);
    var escape = env.getFilter('escape');

    for (var i = 0; i < keys.length; i++) {
      obj[keys[i]] = escape(obj[keys[i]]);
    }

    return interpolate(fmt, obj, named);
  });

  env.addFilter('urlparams', function(url, params) {
    if (url) {
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
      for (var i = 0; i < keys.length; i++) {
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
      return ' class="selected" ';
    }
    return '';
  });

  env.addFilter('stringify', function(obj) {
    return JSON.stringify(obj);
  });

  k.nunjucksEnv = env;
})(jQuery);
