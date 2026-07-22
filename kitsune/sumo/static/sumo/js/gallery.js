import { ajaxSubmitInput, abortUpload } from "sumo/js/ajaxupload";
import KBox from "sumo/js/kbox";
import { apiFetch } from "sumo/js/utils/fetch";

// Show/hide with fade classes (formerly $.fn.showFade/hideFade). Accepts a
// single element or a NodeList/array.
function forEachEl(target, fn) {
  if (!target) {
    return;
  }
  if (target instanceof Element) {
    fn(target);
  } else {
    Array.prototype.forEach.call(target, fn);
  }
}

function showFade(target) {
  forEachEl(target, function (el) {
    el.classList.remove('off');
    el.classList.add('on');
  });
}

function hideFade(target) {
  forEachEl(target, function (el) {
    el.classList.remove('on');
    el.classList.add('off');
  });
}

// A native bubbling CustomEvent so main.js's disableFormsOnSubmit can re-enable
// the form once the async upload/delete completes.
function fireAjaxComplete(form) {
  if (form) {
    form.dispatchEvent(new CustomEvent('ajaxComplete', { bubbles: true }));
  }
}

// Uploads the user cancels mid-flight: the fetch can't be aborted the way the
// old iframe src-reset did, so mark the input and ignore its late completion.
var cancelledUploads = new WeakSet();

function getCsrf() {
  var el = document.querySelector('input[name="csrfmiddlewaretoken"]');
  return el ? el.value : '';
}

document.addEventListener('DOMContentLoaded', function () {
  var mediaTypeSelect = document.getElementById('media-type-select');
  if (mediaTypeSelect) {
    mediaTypeSelect.addEventListener('change', function () {
      window.location = mediaTypeSelect.value;
    });
  }
});

var galleryModal = document.getElementById('gallery-upload-modal');

var CONSTANTS = {
  maxFilenameLength: 70, // truncated on display, if longer
  // the remainder are set by input name, not file type
  messages: {},
  extensions: {
    file: ['jpg', 'jpeg', 'png', 'gif'],
  },
  max_size: {
    file: galleryModal ? galleryModal.dataset.maxImageSize : undefined,
  },
};

var originalPosX, originalPosY;

CONSTANTS.messages.server = gettext('Could not upload file. Please try again later.');
CONSTANTS.messages.file = {
  server: CONSTANTS.messages.server,
  invalid: gettext('Invalid image. Please select a valid image file.'),
  toolarge: gettext('Image too large. Please select a smaller image file.'),
  cancelled: gettext('Upload cancelled. Please select an image file.'),
  deleted: gettext('File deleted. Please select an image file.'),
};

// Save all initial values of input details:
CONSTANTS.messages.initial = {};
document.querySelectorAll('#gallery-upload-modal .upload-media').forEach(function (media) {
  var input = media.querySelector('input');
  var details = media.querySelector('.details');
  if (input) {
    CONSTANTS.messages.initial[input.getAttribute('name')] = details ? details.innerHTML : '';
  }
});

/*
* Tiny helper function returns true/false depending on whether x is in
* array arr.
*/
function in_array(needle, haystack) {
  return (Array.prototype.indexOf.call(haystack, needle) !== -1);
}

/*
* This is the core of the gallery upload process. (See the original docstring
* for the method-by-method summary.)
*/
var GalleryUpload = {
  forms: { image: document.getElementById('gallery-upload-image') },
  modal: document.getElementById('gallery-upload-modal'),

  init: function () {
    var self = this;
    if (!self.modal || !self.forms.image) {
      return;
    }
    showFade(self.forms.image);

    // Bind cancel upload event.
    self.modal.querySelectorAll('.progress a').forEach(function (a) {
      a.addEventListener('click', function (ev) {
        var type = a.dataset.type;
        ev.preventDefault();
        self.cancelUpload(a);
        var form = a.closest('.upload-form');
        self.setInputMessage(
          form ? form.querySelector('input[name="' + type + '"]') : null,
          'cancelled'
        );
      });
    });

    // Bind ajax uploads for inputs
    self.modal.querySelectorAll('input[type="file"]').forEach(function (file) {
      var uploadForm = file.closest('.upload-form');
      // Detach the file input from the publish form: the file is uploaded
      // async, so it must not take part in the form's validation/submission
      // (the old code moved it into its own <form>). Otherwise, once it's
      // hidden + emptied after upload, its `required` blocks the native submit
      // with no visible validation message. `validateForm` still enforces that
      // an image is uploaded before publishing.
      file.setAttribute('form', 'gallery-file-detached');
      ajaxSubmitInput(file, {
        url: uploadForm ? uploadForm.dataset.postUrl : undefined,
        beforeSubmit: function (input) {
          if (!self.isValidFile(input)) {
            self.uploadError(input, 'invalid');
            return false;
          }
          if (self.isTooLarge(input)) {
            self.uploadError(input, 'toolarge');
            return false;
          }
          return self.startUpload(input);
        },
        onComplete: function (input, content, options) {
          fireAjaxComplete(input.closest('form'));
          // Clear just the file input (the old code reset its wrapper form),
          // leaving the main form's metadata fields intact.
          input.value = '';
          if (cancelledUploads.has(input)) {
            cancelledUploads.delete(input);
            return;
          }
          self.uploadComplete(input, content, options);
        },
      });
    });

    // Metadata should be required.
    self.modal.querySelectorAll('.metadata input, .metadata textarea').forEach(function (el) {
      el.setAttribute('required', 'required');
    });

    // Closing the modal with top-right X cancels upload drafts
    self.modal.addEventListener('click', function (e) {
      var close = e.target.closest('a.close');
      if (!close || !self.modal.contains(close)) {
        return;
      }
      var cancels = self.modal.querySelectorAll('input[name="cancel"]');
      if (cancels.length) {
        cancels[cancels.length - 1].click();
      }
    });

    // Submitting the form should call for validation first.
    function validateSubmit(ev) {
      if (!self.validateForm(ev.target)) {
        ev.preventDefault();
      }
    }
    self.forms.image.querySelectorAll('input[name="upload"]').forEach(function (btn) {
      btn.addEventListener('click', validateSubmit);
    });

    if (self.forms.image.classList.contains('draft')) {
      self.draftSetup();
    } else {
      self.modalReset();
    }
  },

  /*
  * Validates the entire upload form before publishing a draft.
  */
  validateForm: function (input) {
    var self = this;
    var form = input.closest('.upload-form');
    // An image must be uploaded. Use :scope so the form's OWN `on` class isn't
    // treated as the `.on` ancestor (native querySelectorAll, unlike jQuery's
    // .find(), matches the ancestor part against the whole document) - otherwise
    // this always matches the file input and blocks publishing.
    if (form === self.forms.image && form.querySelectorAll(':scope .on input[type="file"]').length) {
      return false;
    }
    return true;
  },

  /*
  * Validates uploaded file meets criteria (correct extension).
  */
  isValidFile: function (input) {
    var file = input.files[0];
    var type = input.getAttribute('name');
    var file_ext = file.name.split(/\./).pop().toLowerCase();
    return in_array(file_ext, CONSTANTS.extensions[type]);
  },

  isTooLarge: function (input) {
    var file = input.files[0];
    var type = input.getAttribute('name');
    return file.size >= CONSTANTS.max_size[type];
  },

  /*
  * Fired when upload starts. Hides the file input, shows progress + metadata,
  * returns the truncated filename for later use.
  */
  startUpload: function (input) {
    cancelledUploads.delete(input);
    var form = input.closest('.upload-form');
    var type = input.getAttribute('name');
    var filename = input.value.split(/[/\\]/).pop();
    var progress = Array.prototype.filter.call(
      form.querySelectorAll('.progress'),
      function (p) { return p.classList.contains(type); }
    )[0];
    // truncate filename
    if (filename.length > CONSTANTS.maxFilenameLength) {
      filename = filename.substr(0, CONSTANTS.maxFilenameLength) + '...';
    }
    hideFade(form.querySelector('.upload-media.' + type));
    var message = interpolate(gettext('Uploading "%s"...'), [filename]);
    if (progress) {
      var msgEl = progress.querySelector('.progress-message');
      if (msgEl) {
        msgEl.textContent = message;
      }
      showFade(progress);
    }
    form.querySelectorAll('.metadata').forEach(function (el) {
      el.style.display = '';
    });
    return { filename: filename };
  },

  /*
  * Dispatches to uploadError or uploadSuccess depending on the response.
  */
  uploadComplete: function (input, content, options) {
    if (!content) {
      return;
    }
    var self = this;
    var json;
    try {
      json = JSON.parse(content);
    } catch (err) {
      self.uploadError(input, 'server');
      return;
    }

    if (json.status !== 'success') {
      self.uploadError(input, 'invalid');
      return;
    }
    // Success!
    self.uploadSuccess(input, json, options.filename);
  },

  /*
  * Fired after a successful upload: hide progress, show an image preview,
  * create the cancel button.
  */
  uploadSuccess: function (input, json, filename) {
    var self = this;
    var type = input.getAttribute('name');
    var form = input.closest('.upload-form');
    var upFile = json.file;

    // Upload is no longer in progress.
    hideFade(form.querySelector('.progress.' + type));

    // generate preview
    var content = null;
    if (type === 'file') {
      content = document.createElement('img');
      content.className = 'preview';
      content.setAttribute('alt', upFile.name);
      content.setAttribute('title', upFile.name);
      content.setAttribute('src', upFile.thumbnail_url);
    }

    var previewArea = form.querySelector('.preview.' + type);
    var previewImageContainer = previewArea ? previewArea.querySelector('.preview-image') : null;
    var previewImage = previewImageContainer ? previewImageContainer.querySelector('img') : null;
    if (content && previewImageContainer) {
      if (previewImage) {
        previewImage.replaceWith(content);
      } else {
        previewImageContainer.appendChild(content);
      }
    }

    // Create cancel button.
    form.querySelectorAll('input[name="cancel"]').forEach(function (cancel) {
      self.makeCancelUpload(cancel);
    });

    // Show the preview area and make it a draft.
    showFade(previewArea);
    form.classList.add('draft');
    form.querySelectorAll('input[name="upload"]').forEach(function (btn) {
      btn.disabled = false;
    });
  },

  /*
  * Display a message next to the file input.
  */
  setInputMessage: function (input, reason) {
    if (!input) {
      return;
    }
    var type = input.getAttribute('name');
    var message = CONSTANTS.messages[type][reason];
    document.querySelectorAll('.upload-media.' + type + ' div.details').forEach(function (details) {
      details.innerHTML = message;
    });
  },

  /*
  * Cancel an existing upload and show an error message.
  */
  uploadError: function (input, reason) {
    var self = this;
    var type = input.getAttribute('name');
    // Cancel existing upload.
    document.querySelectorAll('.progress.' + type + ' a.' + type).forEach(function (a) {
      a.click();
    });
    // Show an error message.
    self.setInputMessage(input, reason);
  },

  /*
  * Deleting an uploaded image: hide the preview, POST the delete, show the
  * file input again with a message.
  */
  deleteUpload: function (input) {
    var self = this;
    var mediaForm = input.closest('.upload-form');
    var type = input.dataset.name;
    // Clean up all the preview and progress information.
    if (mediaForm) {
      hideFade(mediaForm.querySelector('.preview.' + type));
    }

    // Send delete request; ignore the response, nothing to do.
    apiFetch(input.dataset.action, {
      method: 'POST',
      data: { csrfmiddlewaretoken: getCsrf() },
      dataType: 'json',
    }).catch(function () {});

    self.setInputMessage(
      mediaForm ? mediaForm.querySelector('input[name="' + type + '"]') : null,
      'deleted'
    );
    self._reUpload(mediaForm, type);
  },

  /*
  * Cancel an upload that's in progress (or just close): hide the progress,
  * show the file input.
  */
  cancelUpload: function (a) {
    var self = this;
    var type = a.dataset.type;
    var form = a.closest('form');
    var input = form ? form.querySelector('input[name="' + type + '"]') : null;
    if (input) {
      // Abort the in-flight upload (the fetch equivalent of the old iframe
      // src-reset) so the server doesn't save an orphaned draft, and ignore its
      // completion if the abort lands too late to stop it.
      cancelledUploads.add(input);
      abortUpload(input);
    }
    var mediaForm = a.closest('.upload-form') || form;
    if (mediaForm) {
      hideFade(mediaForm.querySelector('.progress.' + type));
      self._reUpload(mediaForm, type);
    }
  },

  /*
  * Common code for re-uploading: if nothing else is/has uploaded, hide the
  * metadata fields; always show the file input again.
  */
  _reUpload: function (form, type) {
    if (!form) {
      return;
    }
    var preview = form.querySelector('.preview');
    var hasUpload = !!(preview && preview.classList.contains('on'));
    var progress = form.querySelector('.progress');
    var uploading = !!(progress && progress.classList.contains('on'));
    if (!uploading && !hasUpload) {
      form.querySelectorAll('.metadata').forEach(function (el) {
        el.style.display = 'none';
      });
      form.classList.remove('draft');
    }
    // finally, show the input again
    showFade(form.querySelector('.upload-media.' + type));
    form.querySelectorAll('input[name="upload"]').forEach(function (btn) {
      btn.disabled = !hasUpload;
    });
  },

  /*
  * If there is a draft, fired from init().
  */
  draftSetup: function () {
    var self = this;
    hideFade(self.modal.querySelectorAll('.progress'));
    self.modal.querySelectorAll('input[type="file"]').forEach(function (fileInput) {
      var type = fileInput.getAttribute('name');
      var form = fileInput.closest('.upload-form');
      if (form.dataset[type]) {
        hideFade(form.querySelector('.upload-media.' + type));
      } else {
        showFade(form.querySelector('.upload-media.' + type));
      }
    });
    if (self.forms.image.classList.contains('draft')) {
      hideFade(self.forms.image.querySelectorAll('.upload-media'));
    }
    self.modal.querySelectorAll('input[name="cancel"]').forEach(function (cancel) {
      if (!cancel.classList.contains('kbox-cancel')) {
        self.makeCancelUpload(cancel);
      }
    });
  },

  /*
  * Wire a cancel <input> to delete its upload on click (formerly the
  * jQuery.fn.makeCancelUpload extension).
  */
  makeCancelUpload: function (input) {
    var self = this;
    if (!input || input.tagName !== 'INPUT') {
      return;
    }
    input.addEventListener('click', function (ev) {
      ev.preventDefault();
      self.deleteUpload(input);
    });
  },

  /*
  * Fired when the user closes the modal: delete the selected draft, reset.
  */
  modalClose: function () {
    var self = this;
    // Abort any in-flight uploads first: closing mid-upload otherwise skips the
    // draft cancel below (there's no `.draft` yet) and the upload would land and
    // orphan a draft.
    self.modal.querySelectorAll('input[type="file"]').forEach(function (input) {
      abortUpload(input);
    });
    var cancelInput = self.modal.querySelector('.upload-action input[name="cancel"]');
    if (self.modal.querySelector('.draft')) {
      // If there's a draft to cancel.
      apiFetch(cancelInput ? cancelInput.dataset.action : undefined, {
        method: 'POST',
        data: { csrfmiddlewaretoken: getCsrf() },
        dataType: 'json',
      }).catch(function () {});
    }
    self.modalReset();
  },

  /*
  * Reset all form elements and clean up.
  */
  modalReset: function () {
    var self = this;
    self.modal.querySelectorAll('.draft').forEach(function (el) {
      el.classList.remove('draft');
    });
    // Hide metadata
    self.modal.querySelectorAll('.metadata').forEach(function (el) {
      el.style.display = 'none';
    });
    // Clean up all the preview and progress information.
    hideFade(self.modal.querySelectorAll('.progress, .preview'));
    // Show all the file inputs with default messages.
    var uploads = self.modal.querySelectorAll('.upload-media');
    uploads.forEach(function (media) {
      var input = media.querySelector('input[type="file"]');
      var type = input ? input.getAttribute('name') : null;
      var form = input ? input.closest('form') : null;
      if (form) {
        form.reset();
      }
      var details = media.querySelector('.details');
      if (details && type) {
        details.innerHTML = CONSTANTS.messages.initial[type];
      }
      media.querySelectorAll('.error').forEach(function (el) {
        el.classList.remove('error');
      });
    });
    uploads.forEach(showFade);
    // Cancel all uploads in progress.
    self.modal.querySelectorAll('.progress a').forEach(function (a) {
      self.cancelUpload(a);
    });
    // Reset the form.
    self.forms.image.reset();
  },
};

// Initialize GalleryUpload and kbox
GalleryUpload.init();

if (galleryModal) {
  new KBox(galleryModal, {
    position: 'none',
    preOpen: function () {
      originalPosX = window.scrollX;
      originalPosY = window.scrollY;
      window.scroll({ top: 0 });
      return true;
    },
    preClose: function () {
      window.scroll(originalPosX, originalPosY);
      GalleryUpload.modalClose();
      return true;
    },
  });
}

// Open modal window from media page. Use a native click: KBox's open trigger
// is now a native addEventListener handler, which jQuery's .trigger('click')
// doesn't reliably invoke.
if (document.location.hash === '#upload' ||
  (document.getElementById('gallery-upload-type') && document.getElementById('gallery-upload-type').classList.contains('draft')) ||
  document.body.classList.contains('submitted')) {
  var btnUpload = document.getElementById('btn-upload');
  if (btnUpload) {
    btnUpload.click();
  }
}
