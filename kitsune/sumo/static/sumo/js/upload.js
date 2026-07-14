import { ajaxSubmitInput, wrapDeleteInput } from "sumo/js/ajaxupload";
import dialogSet from "sumo/js/upload-dialog";
import KBox from "sumo/js/kbox";

var UPLOAD = {
  max_filename_length: 80, // max filename length in characters
  error_title_up: gettext("Error uploading image"),
  error_title_del: gettext("Error deleting image"),
  error_login: gettext("Please check you are signed in, and try again."),
};

// A native bubbling CustomEvent so main.js's disableFormsOnSubmit can re-enable
// the form once the async upload/delete completes.
function fireAjaxComplete(form) {
  if (form) {
    form.dispatchEvent(new CustomEvent("ajaxComplete", { bubbles: true }));
  }
}

function init() {
  document.querySelectorAll("div.attachments-list input.delete").forEach(function (input) {
    var form = input.closest("form");
    wrapDeleteInput(input, {
      error_title_del: UPLOAD.error_title_del,
      error_login: UPLOAD.error_login,
      onComplete: function () {
        fireAjaxComplete(form);
      },
    });
  });

  // Upload a file on input value change
  document.querySelectorAll('div.attachments-upload input[type="file"]').forEach(function (fileInput) {
    var form = fileInput.closest("form");
    if (form) {
      form.removeAttribute("enctype");
    }
    var uploadDiv = fileInput.closest(".attachments-upload");
    ajaxSubmitInput(fileInput, {
      url: uploadDiv ? uploadDiv.dataset.postUrl : undefined,
      beforeSubmit: function (input) {
        var divUpload = input.closest(".attachments-upload");
        var opts = {
          progress: divUpload.querySelector(".upload-progress"),
          add: divUpload.querySelector(".add-attachment"),
          adding: divUpload.querySelector(".adding-attachment"),
          loading: divUpload.querySelector(".uploaded"),
        };

        // truncate filename
        opts.filename = input.value.split(/[/\\]/).pop();
        if (opts.filename.length > UPLOAD.max_filename_length) {
          opts.filename = opts.filename.substr(0, UPLOAD.max_filename_length - 3) + "...";
        }

        if (opts.add) {
          opts.add.style.display = "none";
        }
        if (opts.adding) {
          opts.adding.textContent = interpolate(gettext('Uploading "%s"...'), [opts.filename]);
          opts.adding.style.display = "";
        }
        if (opts.loading) {
          opts.loading.classList.remove("empty");
        }
        if (opts.progress) {
          opts.progress.classList.add("show");
        }
        return opts;
      },
      onComplete: function (input, content, opts) {
        var uploadForm = input.closest("form");
        if (uploadForm) {
          uploadForm.reset();
        }
        if (!content) {
          return;
        }

        var json;
        try {
          json = JSON.parse(content);
        } catch (err) {
          dialogSet(UPLOAD.error_login, UPLOAD.error_title_up);
          return;
        }

        if (opts.progress) {
          opts.progress.classList.remove("show");
        }

        if (json.status === "success") {
          var upFile = json.file;
          // HTML decode the name.
          var decoder = document.createElement("div");
          decoder.innerHTML = upFile.name;
          upFile.name = decoder.textContent;

          // <div class="attachment"><input class="delete"/><a class="image"><img/></a></div>
          var attachment = document.createElement("div");
          attachment.className = "attachment";
          var anchor = document.createElement("a");
          anchor.className = "image";
          anchor.setAttribute("href", upFile.url);
          var img = document.createElement("img");
          img.setAttribute("alt", upFile.name);
          img.setAttribute("title", upFile.name);
          img.setAttribute("width", upFile.width);
          img.setAttribute("height", upFile.height);
          img.setAttribute("src", upFile.thumbnail_url);
          anchor.appendChild(img);
          attachment.appendChild(anchor);

          var del = document.createElement("input");
          del.type = "submit";
          del.className = "delete";
          del.setAttribute("data-url", upFile.delete_url);
          del.value = "✖";
          attachment.insertBefore(del, attachment.firstChild);

          if (opts.progress && opts.progress.parentNode) {
            opts.progress.parentNode.insertBefore(attachment, opts.progress);
          }

          wrapDeleteInput(del, {
            error_title_del: UPLOAD.error_title_del,
            error_login: UPLOAD.error_login,
            onComplete: function () {
              fireAjaxComplete(form);
            },
          });
        } else {
          dialogSet(json.message, UPLOAD.error_title_up);
        }

        if (opts.adding) {
          opts.adding.style.display = "none";
        }
        if (opts.add) {
          opts.add.style.display = "";
        }

        fireAjaxComplete(form);
      },
    });
  });

  initImageModal();
}

// hijack the click on the thumb and open modal kbox
function initImageModal() {
  document.querySelectorAll("article").forEach(function (article) {
    article.addEventListener("click", function (ev) {
      var link = ev.target.closest(".attachments-list a.image");
      if (!link || !article.contains(link)) {
        return;
      }
      ev.preventDefault();
      // There may be more than one article element when bubbling up.
      ev.stopPropagation();
      var originalPosX, originalPosY;
      var imgUrl = link.getAttribute("href");
      var html = `<img class="image-attachment" src="${imgUrl}" />`;
      var kbox = new KBox(html, {
        modal: true,
        title: gettext("Image Attachment"),
        id: "image-attachment-kbox",
        destroy: true,
        position: "none", // Disable automatic positioning
        closeOnOutClick: true,
        closeOnEsc: true,
        preOpen: function () {
          originalPosX = window.scrollX;
          originalPosY = window.scrollY;
          window.scroll({ top: 0 });
          return true;
        },
        preClose: function () {
          window.scroll(originalPosX, originalPosY);
          return true;
        },
      });
      kbox.open();
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
