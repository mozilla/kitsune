import KBox from "sumo/js/kbox";

export default function dialogSet(inner, title) {
  var kbox = new KBox($('<p/>').text(inner), {
    title: title,
    destroy: true,
    closeOnOutClick: true,
    modal: true,
    id: 'upload-dialog',
    container: $('body')
  });
  kbox.open();
}
