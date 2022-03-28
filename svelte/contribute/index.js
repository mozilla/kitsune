import Contribute from "./Contribute";

new Contribute({
  target: document.querySelector("#svelte"),
  hydrate: true,
  props: { locale: window.location.pathname.split("/")[1] },
});