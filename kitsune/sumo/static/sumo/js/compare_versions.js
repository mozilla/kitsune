(function() {
  var compareVersions = function(a, b) {
    var a = a.split('.');
    var b = b.split('.');
    var len = Math.max(a.length, b.length);

    for (var i=0; i < len; i++) {
      if ((a[i] && !b[i] && parseInt(a[i]) > 0) || (parseInt(a[i]) > parseInt(b[i]))) {
        return 1;
      } else if ((b[i] && !a[i] && parseInt(b[i]) > 0) || (parseInt(a[i]) < parseInt(b[i]))) {
        return -1;
      }
    }

    return 0;
  };

  window.k = window.k || {};
  window.k.compareVersions = compareVersions;
})();
