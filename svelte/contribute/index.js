import { hydrate } from "svelte";
import Contribute from "./Contribute.svelte";

hydrate(Contribute, {
  target: document.querySelector("#svelte"),
  props: { locale: window.location.pathname.split("/")[1] },
});
