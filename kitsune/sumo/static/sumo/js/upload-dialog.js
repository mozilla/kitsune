import KBox from "sumo/js/kbox";

export default function dialogSet(inner, title) {
  var p = document.createElement("p");
  p.textContent = inner;
  var kbox = new KBox(p, {
    title: title,
    destroy: true,
    closeOnOutClick: true,
    modal: true,
    id: "upload-dialog",
    container: document.body,
  });
  kbox.open();
}
