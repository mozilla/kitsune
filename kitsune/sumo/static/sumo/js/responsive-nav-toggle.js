var nav = document.querySelector('.responsive-nav-wrap');
var navToggle = document.querySelectorAll('[data-toggle-nav]');

function toggleMobileNav(e){
  nav.classList.toggle('is-open');
  document.body.classList.toggle('lock-body');
  e.preventDefault();
};

if (navToggle) {
  navToggle.forEach(function(e) {
    this.addEventListener("click", toggleMobileNav);
  });
}


// dropdown toggle, only active when open.
var parentToggle = document.querySelectorAll('.dropdown > a');

function toggleMobileSubNav(e) {
  this.closest('.dropdown').classList.toggle('is-open');
  e.preventDefault();
  console.log('is there anything here', this.closest('.dropdown'));
};

if (parentToggle) {
  parentToggle.forEach(function(e) {
    this.addEventListener("click", toggleMobileSubNav);
  });
}
