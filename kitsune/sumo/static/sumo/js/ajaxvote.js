/*
* Voting form ajaxified.
*/

export default function AjaxVote(form, options) {
  /* Args:
  * form - the voting form to ajaxify. Can be a selector, DOM element,
  *        or jQuery node
  * options - dict of options
  *      positionMessage - absolutely position the response message?
  *      removeForm - remove the form after vote?
  */
  AjaxVote.prototype.init.call(this, form, options);
}

(function ($) {

  'use strict';

  AjaxVote.prototype = {
    init: function (form, options) {
      var self = this,
        $ajaxForm = $(form),
        $btns = $ajaxForm.find('[type="submit"], [data-type="submit"]');

      options = $.extend({
        positionMessage: false,
        removeForm: false,
        replaceFormWithMessage: false
      }, options);
      self.options = options;
      self.voted = false;
      self.$form = $ajaxForm;

      $btns.on('click', function (e) {
        if (!self.voted) {
          var $btn = $(this),
            $form = $btn.closest('form'),
            url = $form.attr('action'),
            formDataArray = $form.serializeArray(),
            data = { url },
            i, l;
          $btns.attr('disabled', 'disabled');
          $form.addClass('busy');
          for (i = 0, l = formDataArray.length; i < l; i++) {
            data[formDataArray[i].name] = formDataArray[i].value;
          }
          data[$btn.attr('name')] = $btn.val();
          $.ajax({
            url: url,
            type: 'POST',
            data: data,
            dataType: 'json',
            success: function (response) {
              if (response.survey) {
                self.showSurvey(response.survey, $form.parent());
              }
              if (response.message) {
                self.showMessage(response.message, $btn, $form);
              }
              $btn.addClass('active');
              $btns.prop("disabled", false);
              $form.removeClass('busy');
              self.voted = true;

              if (!data.ignored) {
                document.dispatchEvent(new CustomEvent("vote", { bubbles: true, detail: data }));
              }

              // Hide other forms
              self.$form.filter(function () { return !$form.is(this); }).remove();
            },
            error: function () {
              var msg = gettext('There was an error submitting your vote.');
              self.showMessage(msg, $btn, $form);
              $btns.prop("disabled", false);
              $form.removeClass('busy');
            }
          });
        }

        $(this).trigger('blur');
        e.preventDefault();
        return false;
      });
    },
    showMessage: function (message, $showAbove, $form) {
      var self = this,
        $html = $('<div class="ajax-vote-box"><p class="msg document-vote--heading"></p></div>'),
        offset = $showAbove.offset();
      $html.find('p').html(message);

      if (self.options.positionMessage) {
        // on desktop browsers we use absolute positioning
        $('body').append($html);
        $html.css({
          top: offset.top - $html.height() - 30,
          left: offset.left + $showAbove.width() / 2 - $html.width() / 2
        });
        var timer = setTimeout(fadeOut, 10000);
        $('body').one('click', fadeOut);
      } else if (self.options.replaceFormWithMessage) {
        $form.replaceWith($html.removeClass('ajax-vote-box'));
      } else {
        // on mobile browsers we just append to the grandfather
        // TODO: make this more configurable with an extra option
        $showAbove.parent().parent()
          .addClass($showAbove.val()).append($html);
      }

      function fadeOut() {
        $html.fadeOut(function () {
          $html.remove();
        });
        if (self.options.removeForm) {
          self.$form.fadeOut(function () {
            self.$form.remove();
          });
        }
        $('body').off('click', fadeOut);
        clearTimeout(timer);
      }
    },
    showSurvey: function (survey, $container) {
      var $survey = $(survey);
      var $commentCount = $survey.find('#remaining-characters');
      var $commentBox = $survey.find('textarea');
      var maxCount = parseInt($commentCount.text(), 10);
      var $radios = $survey.find('input[type=radio][name=unhelpful-reason]');
      var $submit = $survey.find('[type=submit], [data-type=submit]');
      var $reason = $survey.find('.disabled-reason');
      var $textbox = $survey.find('textarea');

      $container.after($survey);

      // remove the extra message when the survey opens.
      $container.remove();

      // Dispatch a custom "survey-loaded" event to allow other code to add event
      // listeners to the survey, now that it has been freshly loaded into the DOM.
      document.dispatchEvent(new CustomEvent("survey-loaded", { bubbles: true }));

      $submit.prop('disabled', true);

      function validate() {
        var checked = $radios.filter(':checked').val();
        var feedback = $textbox.val();
        if (checked === undefined ||
          ((checked === 'other' || checked === 'firefox-feedback') && !feedback)) {
          $submit.prop('disabled', true);
          $reason.fadeIn(600);
        } else {
          $submit.prop('disabled', false);
          $reason.fadeOut(600);
        }
      }

      $commentBox.on('input', function () {
        var currentCount = $commentBox.val().length;
        var checked;

        if (maxCount - currentCount >= 0) {
          $commentCount.text(maxCount - currentCount);
        } else {
          $commentCount.text(0);
          $commentBox.val($commentBox.val().substr(0, maxCount));
        }
        validate();
      });

      $radios.on('change', validate);

      new AjaxVote($survey.find('form'), {
        replaceFormWithMessage: true
      });
    }
  };

})(jQuery);
