/*
 * Voting form ajaxified.
 */

import { apiFetch } from "sumo/js/utils/fetch";
import { fadeOut, serialize, toElements } from "sumo/js/utils/dom";

export default function AjaxVote(form, options) {
  /* Args:
  * form - the voting form(s) to ajaxify. Can be a selector, DOM element,
  *        NodeList/array, or (during the jQuery transition) a jQuery object.
  * options - dict of options
  *      positionMessage - absolutely position the response message?
  *      removeForm - remove the form after vote?
  */
  AjaxVote.prototype.init.call(this, form, options);
}

AjaxVote.prototype = {
  init: function (form, options) {
    var self = this;
    var forms = toElements(form);
    var btns = [];
    forms.forEach(function (f) {
      btns = btns.concat(
        Array.from(f.querySelectorAll('[type="submit"], [data-type="submit"]'))
      );
    });

    self.options = Object.assign(
      {
        positionMessage: false,
        removeForm: false,
        replaceFormWithMessage: false,
      },
      options
    );
    self.voted = false;
    self.forms = forms;
    self.btns = btns;

    btns.forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        if (!self.voted) {
          var voteForm = btn.closest("form");
          var url = voteForm.getAttribute("action");
          var data = Object.assign({ url: url }, serialize(voteForm));
          data[btn.name] = btn.value;

          btns.forEach(function (b) {
            b.disabled = true;
          });
          voteForm.classList.add("busy");

          apiFetch(url, { method: "POST", data: data, dataType: "json" })
            .then(function (response) {
              if (response.survey) {
                self.showSurvey(response.survey, voteForm.parentNode);
              }
              if (response.message) {
                self.showMessage(response.message, btn, voteForm);
              }
              btn.classList.add("active");
              btns.forEach(function (b) {
                b.disabled = false;
              });
              voteForm.classList.remove("busy");
              self.voted = true;

              if (!data.ignored) {
                document.dispatchEvent(
                  new CustomEvent("vote", { bubbles: true, detail: data })
                );
              }

              // Hide the other forms in the set.
              self.forms.forEach(function (f) {
                if (f !== voteForm) {
                  f.remove();
                }
              });
            })
            .catch(function () {
              var msg = gettext("There was an error submitting your vote.");
              self.showMessage(msg, btn, voteForm);
              btns.forEach(function (b) {
                b.disabled = false;
              });
              voteForm.classList.remove("busy");
            });
        }

        btn.blur();
        e.preventDefault();
      });
    });
  },

  showMessage: function (message, showAbove, form) {
    var self = this;
    var box = document.createElement("div");
    box.className = "ajax-vote-box";
    var p = document.createElement("p");
    p.className = "msg document-vote--heading";
    p.innerHTML = message;
    box.appendChild(p);

    var timer;
    var faded = false;
    function doFadeOut() {
      if (faded) {
        return;
      }
      faded = true;
      fadeOut(box).then(function () {
        box.remove();
      });
      if (self.options.removeForm) {
        self.forms.forEach(function (f) {
          fadeOut(f).then(function () {
            f.remove();
          });
        });
      }
      document.body.removeEventListener("click", doFadeOut);
      clearTimeout(timer);
    }

    if (self.options.positionMessage) {
      // on desktop browsers we use absolute positioning
      document.body.appendChild(box);
      var rect = showAbove.getBoundingClientRect();
      var top = rect.top + window.pageYOffset;
      var left = rect.left + window.pageXOffset;
      box.style.top = top - box.offsetHeight - 30 + "px";
      box.style.left =
        left + showAbove.offsetWidth / 2 - box.offsetWidth / 2 + "px";
      timer = setTimeout(doFadeOut, 10000);
      document.body.addEventListener("click", doFadeOut, { once: true });
    } else if (self.options.replaceFormWithMessage) {
      box.classList.remove("ajax-vote-box");
      form.replaceWith(box);
    } else {
      // on mobile browsers we just append to the grandfather
      // TODO: make this more configurable with an extra option
      var grandparent = showAbove.parentNode.parentNode;
      grandparent.classList.add(showAbove.value);
      grandparent.appendChild(box);
    }
  },

  showSurvey: function (survey, container) {
    var template = document.createElement("template");
    template.innerHTML = typeof survey === "string" ? survey.trim() : "";
    var surveyEl =
      template.content.firstElementChild || toElements(survey)[0];

    var commentCount = surveyEl.querySelector("#remaining-characters");
    var commentBox = surveyEl.querySelector("textarea");
    var maxCount = parseInt(commentCount.textContent, 10);
    var radios = surveyEl.querySelectorAll(
      "input[type=radio][name=unhelpful-reason]"
    );
    var submit = surveyEl.querySelector("[type=submit], [data-type=submit]");
    var reason = surveyEl.querySelector(".disabled-reason");
    var textbox = surveyEl.querySelector("textarea");

    container.after(surveyEl);

    // remove the extra message when the survey opens.
    container.remove();

    // Dispatch a custom "survey-loaded" event to allow other code to add event
    // listeners to the survey, now that it has been freshly loaded into the DOM.
    document.dispatchEvent(new CustomEvent("survey-loaded", { bubbles: true }));

    submit.disabled = true;

    function checkedValue() {
      for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) {
          return radios[i].value;
        }
      }
      return undefined;
    }

    function validate() {
      var checked = checkedValue();
      var feedback = textbox.value;
      if (
        checked === undefined ||
        ((checked === "other" || checked === "firefox-feedback") && !feedback)
      ) {
        submit.disabled = true;
        reason.style.display = "";
      } else {
        submit.disabled = false;
        reason.style.display = "none";
      }
    }

    commentBox.addEventListener("input", function () {
      var currentCount = commentBox.value.length;
      if (maxCount - currentCount >= 0) {
        commentCount.textContent = maxCount - currentCount;
      } else {
        commentCount.textContent = 0;
        commentBox.value = commentBox.value.substr(0, maxCount);
      }
      validate();
    });

    radios.forEach(function (radio) {
      radio.addEventListener("change", validate);
    });

    new AjaxVote(surveyEl.querySelector("form"), {
      replaceFormWithMessage: true,
    });
  },
};
