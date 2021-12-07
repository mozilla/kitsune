import questionmarkIcon from "sumo/img/questions/icon.questionmark.png";
/*
* questions.js
* Scripts for the questions app.
*/

// TODO: Figure out how to break out the functionality here into
// testable parts.

(function($) {

  function init() {
    var $body = $('body');

    // if there's an error on page load, focus the field.
    $('.has-error input, .has-error textarea').first().focus();

    if ($body.is('.new-question')) {
      initQuestion();

      if (window.location.search.indexOf('step=aaq-register') > -1) {
        trackEvent('Ask A Question Flow', 'step 1 page');
      } else if (window.location.search.indexOf('step=aaq-question') > -1) {
        trackEvent('Ask A Question Flow', 'step 2 page');
      }
    }

    if ($body.is('.edit-question')) {
      initQuestion("editing");
    }

    if ($body.is('.questions')) {
      initTagFilterToggle();

      $('#flag-filter input[type="checkbox"]').on('click', function() {
        window.location = $(this).data('url');
      });

      if (window.location.pathname.indexOf('questions/new/confirm') > -1) {
        trackEvent('Ask A Question Flow', 'step 3 confirm page');
      }
    }

    if ($body.is('.answers')) {
      // Put last search query into search box
      $('#support-search input[name=q]')
      .val(k.unquote($.cookie('last_search')));

      function takeQuestion() {
        if ($(this).val().length > 0) {
          var $form = $(this).closest('form');
          var url = $form.data('take-question-url');
          var csrftoken = $('input[name=csrfmiddlewaretoken]').val();
          $.ajax({
            url: url,
            method: 'POST',
            beforeSend: function(xhr, settings) {
              xhr.setRequestHeader('X-CSRFToken', csrftoken);
            }
          });
        }
      }

      $('#id_content').on('keyup', _.throttle(takeQuestion, 60000));

      $(document).on('click', '#details-edit', function(ev) {
        ev.preventDefault();
        $('#question-details').addClass('editing');
      });

      initHaveThisProblemTooAjax();
      initHelpfulVote();
      initCrashIdLinking();
      initEditDetails();
      addReferrerAndQueryToVoteForm();
      initReplyToAnswer();
      new k.AjaxPreview($('#preview'));
    }

    Marky.createSimpleToolbar('.editor-tools', '#reply-content, #id_content', {cannedResponses: !$body.is('.new-question')});

    // product selector page reloading
    $('#product-selector select').on('change', function() {
      var val = $(this).val();
      var queryParams = k.getQueryParamsAsDict(document.location.toString());

      if (val === '') {
        delete queryParams.product;
      } else {
        queryParams.product = val;
      }
      document.location = document.location.pathname + '?' + $.param(queryParams);
    });

    // sort questions page reloading
    $('[data-sort-questions]').on('change', function() {
      document.location = $(this).val()
    });

  }

  /*
  * Initialize the new/edit question page/form
  */
  function initQuestion(action) {
    var $questionForm = $('#question-form');
    var aaq = new AAQSystemInfo($questionForm);
    if (action === "editing") {
      $("#troubleshooting-field").show();
    } else {
      hideDetails($questionForm, aaq);
    }
  }

  function isLoggedIn() {
    return $('#greeting span.user').length > 0;
  }

  // Handle changes to the details for a question
  function initEditDetails() {
    $('#details-product').on('change', function() {
      var $selected;

      $(this).children().each(function() {
        if (this.selected) {
          $selected = $(this);
        }
      });

      $('#details-topic').children().remove();
      $('#details-submit').prop('disabled', true);

      $.ajax($selected.data('url'), {
        'dataType': 'json',
        'success': function(data) {
          for (var i = 0; i < data.topics.length; i++) {
            var topic = data.topics[i];
            var $opt = $('<option />');

            $opt.attr('value', topic.id);
            $opt.text(topic.title);

            $('#details-topic').append($opt);
          }
          $('#details-submit').prop('disabled', false);
        }
      });
    });
  }

  // Hide the browser/system details for users on FF with js enabled
  // and are submitting a question for FF on desktop.
  function hideDetails($form, aaq) {
    $form.find('ul').addClass('hide-details');
    $form.find('a.show, a.hide').click(function(ev) {
      ev.preventDefault();
      $(this).closest('li')
      .toggleClass('show')
      .toggleClass('hide')
      .closest('ul')
      .toggleClass('show-details');
    });
  }

  /*
  * Ajaxify any "I have this problem too" forms (may be multiple per page)
  */
  function initHaveThisProblemTooAjax() {
    var $container = $('#question div.me-too, .question-tools div.me-too');

    // ajaxify each form individually so the resulting kbox attaches to
    // the correct DOM element
    $container.each(function() {
      initAjaxForm($(this), 'form', '#vote-thanks');
    });

    $container.find('input').click(function() {
      $(this).attr('disabled', 'disabled');
    });

    // closing or cancelling the kbox on any of the forms should remove
    // all of them
    $container.delegate('.kbox-close, .kbox-cancel', 'click', function(ev) {
      ev.preventDefault();
      $container.unbind().remove();
    });
  }

  function addReferrerAndQueryToVoteForm() {
    // Add the source/referrer and query terms to the helpful vote form
    var urlParams = k.getQueryParamsAsDict(),
      referrer = k.getReferrer(urlParams),
      query = k.getSearchQuery(urlParams, referrer);
    $('form.helpful, .me-too form')
    .append($('<input type="hidden" name="referrer"/>')
    .attr('value', referrer))
    .append($('<input type="hidden" name="query"/>')
    .attr('value', query));
  }

  /*
  * Ajaxify the Helpful/Not Helpful form
  */
  function initHelpfulVote() {
    $('.sumo-l-two-col--sidebar, #document-list, .answer-tools').each(function() {
      new k.AjaxVote($(this).find('form.helpful'), {
        replaceFormWithMessage: true,
        removeForm: true
      });
    });
  }

  // Helper
  function initAjaxForm($container, formSelector, boxSelector, onKboxClose) {
    $container.delegate(formSelector, 'submit', function(ev) {
      ev.preventDefault();
      var $form = $(this);
      var url = $form.attr('action');
      var data = $form.serialize();

      $.ajax({
        url: url,
        type: 'POST',
        data: data,
        dataType: 'json',
        success: function(response) {
          if (response.html) {
            if ($(boxSelector).length === 0) {
              // We don't have a modal set up yet.
              var kbox = new KBox(response.html, {
                container: $container,
                preClose: onKboxClose
              });
              kbox.open();
            } else {
              $(boxSelector).html($(response.html).children());
            }
          } else if (response.message) {
            var html = '<div class="msg"></div>';
            $(boxSelector)
            .html(html)
            .find('.msg').text(response.message);
          }

          if (!response.ignored) {
            // Trigger a document event for others to listen for.
            $(document).trigger('vote', $.extend(data, {url: url}));
          }
        },
        error: function() {
          var message = gettext('There was an error.');
          alert(message);
        }
      });

      return false;
    });
  }

  function initTagFilterToggle() {
    $('#toggle-tag-filter').click(function(e) {
      e.preventDefault();
      $('#tag-filter').slideToggle('fast');  // CSS3: Y U NO TRANSITION TO `height: auto;`?
      $(this).toggleClass('off');
    });
  }

  /*
  * Links all crash IDs found in the passed HTML container elements
  */
  function linkCrashIds(container) {
    if (!container) {
      return;
    }
    var crashIDRegex = new RegExp('(bp-[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', 'g');
    var crashStatsBase = 'https://crash-stats.mozilla.com/report/index/';
    var helpingWithCrashesArticle = '/kb/helping-crashes';
    var crashReportContainer =
    "<span class='crash-report'>" +
    "<a href='" + crashStatsBase + "$1' target='_blank'>$1</a>" +
    "<a href='" + helpingWithCrashesArticle + "' target='_blank'>" +
    "<img src='" + questionmarkIcon + "'></img></a></span>";

    container.html(container.html().replace(crashIDRegex, crashReportContainer));
  }

  // For testing purposes only:
  k.linkCrashIds = linkCrashIds;

  /*
  * Initialize the automatic linking of crash IDs
  */
  function initCrashIdLinking() {
    var postContents = $('.question .main-content, .answer .main-content, #more-system-details');
    postContents.each(function() {
      linkCrashIds($(this));
    });
  }

  function initReplyToAnswer() {
    $('a.quoted-reply').click(function() {
      var contentId = $(this).data('content-id'),
        $content = $('#' + contentId),
        text = $content.find('.content-raw').text(),
        user = $content.find('.display-name').text(),
        reply_text = `''<p>${user} [[#${contentId}|${gettext('said')}]]</p>''\n<blockquote>${text}\n</blockquote>\n\n`,
        $textarea = $('#id_content'),
        oldtext = $textarea.val();

      $textarea.val(oldtext + reply_text);

      setTimeout(function() {
        $textarea.focus();
      }, 10);

      return true;
    });
  }

  $(document).ready(init);

})(jQuery);
