(function() {
  var legacyLoginToggles = document.querySelectorAll('.legacy-login-toggle');
  var loginLegacy = document.getElementById('login-legacy');
  var loginFXA = document.getElementById('login-fxa');

  for (var i = 0; i < legacyLoginToggles.length; i++) {
    legacyLoginToggles[i].onclick = function(e) {
      e.preventDefault();
      loginLegacy.classList.toggle('hidden');
      loginFXA.classList.toggle('hidden');
    };
  }
})();
