/*
 * ajaxupload.js
 *
 * Vanilla replacement for the vendored jquery.ajaxupload plugin. Provides two
 * helpers for uploading/deleting files without leaving the page:
 *   ajaxSubmitInput(input, options) - POST a file input's file(s) via fetch +
 *     FormData (replacing the old hidden-<iframe> form-submit mechanism).
 *   wrapDeleteInput(input, options) - a delete-attachment helper built on it.
 *
 * The CSRF token is sent as the `csrfmiddlewaretoken` form field (exactly as
 * the old wrapped <form> did), so Django's CSRF check still passes.
 */

import dialogSet from "sumo/js/upload-dialog";

/*
 * Takes a file (or submit) input and, on the given event, POSTs its file(s)
 * to options.url via fetch + FormData. Options:
 *   url          - where to POST
 *   accept        - list of MIME types (sets the input's accept attribute)
 *   inputEvent    - event that triggers the upload (default 'change')
 *   beforeSubmit  - called with the input before POSTing; return false to
 *                   cancel, or a value to pass through to onComplete
 *   onComplete    - called with (input, responseText, beforeSubmitResult, ok)
 *                   when the request finishes. responseText is null on a
 *                   network error (mirroring the old empty-iframe case); ok is
 *                   response.ok - false on a network error or a non-2xx status
 *                   - so callers can tell an HTTP failure from a success.
 */
export function ajaxSubmitInput(input, options) {
  // Only works on <input/>
  if (!input || input.tagName !== "INPUT") {
    return input;
  }

  options = Object.assign(
    {
      url: "/upload",
      accept: false,
      inputEvent: "change",
      beforeSubmit: function () {},
      onComplete: function () {},
    },
    options
  );

  if (options.accept) {
    input.setAttribute("accept", options.accept);
  }

  input.addEventListener(options.inputEvent, function (ev) {
    // The old code isolated the input in its own <form>; here we stop the
    // input's default (e.g. a submit button submitting an ancestor form).
    ev.preventDefault();

    var passThrough = options.beforeSubmit(input);
    if (passThrough === false) {
      return;
    }

    var formData = new FormData();
    if (input.type === "file" && input.files) {
      Array.prototype.forEach.call(input.files, function (file) {
        formData.append(input.name, file, file.name);
      });
    }
    var csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) {
      formData.append("csrfmiddlewaretoken", csrfInput.value);
    }

    fetch(options.url, { method: "POST", body: formData })
      .then(function (response) {
        var ok = response.ok;
        return response.text().then(function (text) {
          options.onComplete(input, text, passThrough, ok);
        });
      })
      .catch(function () {
        options.onComplete(input, null, passThrough, false);
      });
  });

  return input;
}

/*
 * Wrap a delete <input> and bind delete handling to its click: confirm, dim the
 * attachment, POST the delete, then remove the attachment (or show an error).
 */
export function wrapDeleteInput(input, options) {
  // Only works on <input/>
  if (!input || input.tagName !== "INPUT") {
    return input;
  }

  options = Object.assign(
    {
      error_title_del: gettext("Error deleting"),
      // Shown when the response is OK but unparseable - typically a
      // session-expired redirect to a login page.
      error_login: gettext("Please check you are signed in, and try again."),
      // Shown on an HTTP/transport failure with no usable message.
      error_server: gettext("There was an error. Please try again in a moment."),
      onComplete: function () {},
    },
    options
  );

  var attachment = input.closest(".attachment");
  var image = attachment ? attachment.querySelector(".image") : null;

  ajaxSubmitInput(input, {
    url: input.getAttribute("data-url"),
    inputEvent: "click",
    beforeSubmit: function () {
      if (confirm(gettext("Are you sure you want delete the image?"))) {
        if (attachment) {
          var overlay = attachment.querySelector(".overlay");
          if (!overlay) {
            overlay = document.createElement("div");
            overlay.className = "overlay";
            attachment.appendChild(overlay);
          }
          overlay.style.display = "";
        }
        if (image) {
          image.style.opacity = "0.5";
        }
        return true;
      }
      return false;
    },
    onComplete: function (inp, content, passThrough, ok) {
      var json = null;
      if (content) {
        try {
          json = JSON.parse(content);
        } catch (err) {
          json = null;
        }
      }

      if (json && json.status === "success") {
        if (attachment) {
          attachment.remove();
        }
        options.onComplete();
        return;
      }

      // Any other outcome is a failure: restore the dimmed image and surface a
      // message. Prefer the server's structured message; otherwise show the
      // sign-in hint only when the response was itself OK (a session-expired
      // login redirect) and a generic error on an HTTP/transport failure.
      if (image) {
        image.style.opacity = 1;
      }
      if (json && json.message) {
        dialogSet(json.message, options.error_title_del);
      } else if (ok) {
        dialogSet(options.error_login, options.error_title_del);
      } else {
        dialogSet(options.error_server, options.error_title_del);
      }
    },
  });

  return input;
}
