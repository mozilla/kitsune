/* Python(ish) string formatting:
 * >>> format('{0}', ['zzz'])
 * "zzz"
 * >>> format('{0}{1}', 1, 2)
 * "12"
 * >>> format('{x}', {x: 1})
 * "1"
 * (Stolen from Zamboni.)
 */
var format = (function() {
    var re = /\{([^}]+)\}/g;
    return function(s, args) {
        if (!args) return;
        if (!(args instanceof Array || args instanceof Object))
            args = Array.prototype.slice.call(arguments, 1);
        return s.replace(re, function(_, match){ return args[match]; });
    };
})();
function template(s) {
    return function(args) { return format(s, args); };
}

