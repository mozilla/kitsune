var nav = document.querySelector(".responsive-nav-wrap");
var navToggle = document.querySelectorAll("[data-toggle-nav]");

function toggleMobileNav(e) {
  nav.classList.toggle("is-open");
  document.body.classList.toggle("lock-body");

  var root = document.getElementsByTagName("html")[0];
  root.classList.toggle("lock-body");

  e.preventDefault();
}

if (navToggle) {
  navToggle.forEach(function (e) {
    e.addEventListener("click", toggleMobileNav);
  });
}

var parentToggle = document.querySelectorAll(".dropdown > a");

function toggleMobileSubNav(e) {
  this.closest(".dropdown").classList.toggle("is-open");
  nav.classList.toggle("is-second-level");
  e.preventDefault();
}

if (parentToggle) {
  parentToggle.forEach(function (e) {
    e.addEventListener("click", toggleMobileSubNav);
  });
}
