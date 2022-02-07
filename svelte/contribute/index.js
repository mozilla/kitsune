import Contribute from "./Contribute";

new Contribute({
  target: document.querySelector("#main-content"),
  props: { locale: window.location.pathname.split("/")[1] },
});
