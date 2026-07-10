/*
* Inline editable sections
*/

export function initInlineEditing() {
  // Enable managing of member and leader lists.
  document.querySelectorAll('.editable a.edit').forEach(function(edit) {
    var originalText = edit.textContent;
    edit.addEventListener('click', function(ev) {
      var container = edit.closest('.editable');
      container.classList.toggle('edit-on');
      if (container.classList.contains('edit-on')) {
        edit.textContent = gettext('Cancel');
      } else {
        edit.textContent = originalText;
      }
      ev.preventDefault();
    });
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initInlineEditing);
} else {
  initInlineEditing();
}
