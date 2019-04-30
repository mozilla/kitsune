(function() {
  const legacyLoginToggle = document.getElementById('legacy-login-toggle');
  const loginLegacy = document.getElementById('login-legacy');
  const loginFFX = document.getElementById('login-ffx');

  legacyLoginToggle.onclick = (e) => {
    e.preventDefault();
    loginLegacy.classList.toggle('hidden');
    loginFFX.classList.toggle('hidden');
  };
})();
