// Get current status of the form.
let dataChanged = false;
let doc_inputs = document.querySelectorAll('#document-form input');

function formChanged(e) {
  dataChanged = true;
  e.preventDefault();
}

doc_inputs.forEach(function(e) {
  e.addEventListener('change', formChanged);
});

let submit_button = document.querySelector('#submit-modal');
submit_button.onclick = function() {
  dataChanged = false;
};

window.onbeforeunload = function() {
  if ( dataChanged ) {
    return 'Are you sure you want to leave this page? Data may have not been saved.';
  }
  return;
}
