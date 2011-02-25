/*
 * JavaScript localization fallback for when, say, our messages.[po/mo] are
 * broken.
 *
 * These are largely copied from Django's jsi18n, except they don't reply on
 * the catalog global variable.
 *
 * Include this __after__ the Django script.
 */
if (typeof(catalog) === 'undefined') {
    function gettext(msgid) {
        return msgid;
    }

    function ngettext(singular, plural, count) {
        return (count == 1) ? singular : plural;
    }

    function interpolate(fmt, obj, named) {
      if (named) {
        return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
      } else {
        return fmt.replace(/%s/g, function(match){return String(obj.shift())});
      }
    }
}
