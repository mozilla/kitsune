(function() {
  const legacyLoginToggles = document.querySelectorAll('.legacy-login-toggle');
  const loginLegacy = document.getElementById('login-legacy');
  const loginFFX = document.getElementById('login-ffx');

  for (let legacyLoginToggle of legacyLoginToggles) {
    legacyLoginToggle.onclick = function(e) {
      e.preventDefault();
      loginLegacy.classList.toggle('hidden');
      loginFFX.classList.toggle('hidden');
    };
  }
})();
