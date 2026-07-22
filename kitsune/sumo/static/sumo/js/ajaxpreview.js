/*
 * Wiki content previews - ajaxified.
 *
 * AjaxPreview is an EventTarget. It emits native CustomEvents:
 *   get-preview  - the preview button was clicked
 *   show-preview - the preview HTML has arrived (detail: {success, html})
 *   done         - the preview has been rendered (detail: {success})
 */

import { apiFetch } from "sumo/js/utils/fetch";
import { toElement } from "sumo/js/utils/dom";
import { lazyload } from "sumo/js/utils/lazyload";

function fieldValue(form, selector) {
  if (!form) {
    return undefined;
  }
  const el = form.querySelector(selector);
  return el ? el.value : undefined;
}

// Extend window.EventTarget (not the bare global) so instances and the
// CustomEvents they dispatch come from the same realm in both the browser and
// the jsdom test environment.
export default class AjaxPreview extends window.EventTarget {
  constructor(el, options) {
    /* Args:
     * el - The button/link that triggers the preview (selector, element, or,
     *      during the jQuery transition, a jQuery object)
     * options - dict of options
     *      previewUrl - url to POST the content and get a preview
     *      contentElement - element or selector for the input content
     *      previewElement - element or selector to insert the preview into
     *      changeHash - set document.location.hash to the previewElement id
     *                   (default: true)
     */
    super();

    const self = this;
    const btn = toElement(el);
    if (!btn) {
      return;
    }
    const o = options || {};
    const form = btn.closest("form");
    const previewUrl = o.previewUrl || btn.dataset.previewUrl;
    const preview =
      (o.previewElement && toElement(o.previewElement)) ||
      document.getElementById(btn.dataset.previewContainerId);
    const content =
      (o.contentElement && toElement(o.contentElement)) ||
      document.getElementById(btn.dataset.previewContentId);
    const csrftoken = fieldValue(form, "input[name=csrfmiddlewaretoken]");
    const slug =
      fieldValue(form, "input[name=slug]") || window.location.pathname;
    const locale = fieldValue(form, "[name=locale]");
    const changeHash = o.changeHash === undefined ? true : o.changeHash;

    btn.addEventListener("click", function (e) {
      e.preventDefault();
      btn.setAttribute("disabled", "disabled");
      self.dispatchEvent(new CustomEvent("get-preview"));
    });

    // Trying to make this event driven for easier testability.
    self.addEventListener("get-preview", function () {
      apiFetch(previewUrl, {
        method: "POST",
        data: {
          content: content.value,
          slug: slug,
          locale: locale,
          csrfmiddlewaretoken: csrftoken,
        },
        dataType: "html",
      })
        .then(function (html) {
          self.dispatchEvent(
            new CustomEvent("show-preview", { detail: { success: true, html } })
          );
        })
        .catch(function (error) {
          console.log(error);
          const msg = gettext("There was an error generating the preview.");
          self.dispatchEvent(
            new CustomEvent("show-preview", {
              detail: { success: false, html: msg },
            })
          );
        });
    });

    self.addEventListener("show-preview", function (e) {
      const { success, html } = e.detail;
      preview.innerHTML = html;
      lazyload(preview);
      if (changeHash) {
        document.location.hash = preview.getAttribute("id");
      }
      btn.disabled = false;
      self.dispatchEvent(new CustomEvent("done", { detail: { success } }));
    });
  }
}
