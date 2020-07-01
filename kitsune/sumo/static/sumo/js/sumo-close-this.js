const closeButtons = document.querySelectorAll("[data-close-button]");

closeButtons.forEach(function (e) {
  const closeThis = e.dataset.closeButton;

  e.onclick = function () {
    document.querySelector(closeThis).style.display = "none";
  };
});
