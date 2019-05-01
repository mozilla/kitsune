(function() {
  var legacyLoginToggles = document.querySelectorAll('.legacy-login-toggle');
  var loginLegacy = document.getElementById('login-legacy');
  var loginFFX = document.getElementById('login-ffx');

  for (var i = 0; i < legacyLoginToggles.length; i++) {
    legacyLoginToggles[i].onclick = function(e) {
      e.preventDefault();
      loginLegacy.classList.toggle('hidden');
      loginFFX.classList.toggle('hidden');
    };
  }
})();
