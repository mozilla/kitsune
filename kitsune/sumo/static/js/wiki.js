/*
 * wiki.js
 * Scripts for the wiki app.
 */

(function ($) {
  function init() {
    var $body = $('body');

    $('select.enable-if-js').removeAttr('disabled');

    initPrepopulatedSlugs();
    initDetailsTags();

    if ($body.is('.document')) {  // Document page
      // Put last search query into search box
      $('#support-search input[name=q]')
          .val(k.unquote($.cookie('last_search')));
      ShowFor.initForTags();
      addReferrerAndQueryToVoteForm();
      new k.AjaxVote('.document-vote form', {
        positionMessage: true
      });
      initAOABanner();
    } else if ($body.is('.review')) { // Review pages
      ShowFor.initForTags();
      initNeedsChange();

      $('img.lazy').loadnow();

      // We can enable the buttons now.
      $('#actions input').removeAttr('disabled');
    }

    if ($body.is('.edit, .new, .translate')) { // Document form page
      // Submit form
      $('#id_comment').keypress(function(e) {
        if(e.which == 13) {
          $(this).blur();
          $(this).closest('form').find('input[type=submit]').focus().click();
          return false;
        }
      });
      initExitSupportFor();
      initArticlePreview();
      initPreviewDiff();
      initTitleAndSlugCheck();
      initPreValidation();
      initNeedsChange();
      initSummaryCount();
      initFormLock();
      initAceEditor();

      $('img.lazy').loadnow();

      // We can enable the buttons now.
      $('.submit input').removeAttr('disabled');
    }

    if ($body.is('.edit, .new')) {
      // collapse the topics listing per product and show only one topic list
      // at at a time
        $(function () {
            $("#accordion").accordion({
                collapsible: true,
                heightStyle: "content",
                active: false
            });
        });
    }

    if ($body.is('.translate')) {  // Translate page
      initToggleDiff();
    }

    initEditingTools();

    initDiffPicker();

    Marky.createFullToolbar('.editor-tools', '#id_content');

    initReadyForL10n();

    initArticleApproveModal();

    initRevisionList();

    $('img.lazy').lazyload();
  }

  function initArticleApproveModal() {
    if ($('#approve-modal').length > 0) {
      var onSignificanceClick = function(e) {
        // Hiding if the significance is typo.
        // .parent() is because #id_is_ready_for_localization is inside a
        // <label>, as is the text
        if (e.target.id === 'id_significance_0') {
          $('#id_is_ready_for_localization').parent().hide();
        } else {
          $('#id_is_ready_for_localization').parent().show();
        }
      };

      $('#id_significance_0').click(onSignificanceClick);
      $('#id_significance_1').click(onSignificanceClick);
      $('#id_significance_2').click(onSignificanceClick);
    }
  }

  // Make <summary> and <details> tags work even if the browser doesn't support them.
  // From http://mathiasbynens.be/notes/html5-details-jquery
  function initDetailsTags() {
    // Note <details> tag support. Modernizr doesn't do this properly as of 1.5; it thinks Firefox 4 can do it, even though the tag has no "open" attr.
    if (!('open' in document.createElement('details'))) {
      document.documentElement.className += ' no-details';
    }

    // Execute the fallback only if there's no native `details` support
    if (!('open' in document.createElement('details'))) {
      // Loop through all `details` elements
      $('details').each(function() {
        // Store a reference to the current `details` element in a variable
        var $details = $(this),
        // Store a reference to the `summary` element of the current `details` element (if any) in a variable
            $detailsSummary = $('summary', $details),
        // Do the same for the info within the `details` element
            $detailsNotSummary = $details.children(':not(summary)'),
        // This will be used later to look for direct child text nodes
            $detailsNotSummaryContents = $details.contents(':not(summary)');

        // If there is no `summary` in the current `details` element...
        if (!$detailsSummary.length) {
          // ...create one with default text
          $detailsSummary = $(document.createElement('summary')).text('Details').prependTo($details);
        }

        // Look for direct child text nodes
        if ($detailsNotSummary.length !== $detailsNotSummaryContents.length) {
          // Wrap child text nodes in a `span` element
          $detailsNotSummaryContents.filter(function() {
            // Only keep the node in the collection if it's a text node containing more than only whitespace
            return (this.nodeType === 3) && (/[^\t\n\r ]/.test(this.data));
          }).wrap('<span>');
          // There are now no direct child text nodes anymore -- they're wrapped in `span` elements
          $detailsNotSummary = $details.children(':not(summary)');
        }

        // Hide content unless there's an `open` attribute
        if (typeof $details.attr('open') !== 'undefined') {
          $details.addClass('open');
          $detailsNotSummary.show();
        } else {
          $detailsNotSummary.hide();
        }

        // Set the `tabindex` attribute of the `summary` element to 0 to make it keyboard accessible
        $detailsSummary.attr('tabindex', 0).click(function() {
          // Focus on the `summary` element
          $detailsSummary.focus();
          // Toggle the `open` attribute of the `details` element
          if (typeof $details.attr('open') !== 'undefined') {
            $details.removeAttr('open');
          }
          else {
            $details.attr('open', 'open');
          }
          // Toggle the additional information in the `details` element
          $detailsNotSummary.slideToggle();
          $details.toggleClass('open');
        }).keyup(function(event) {
              if (13 === event.keyCode || 32 === event.keyCode) {
                // Enter or Space is pressed -- trigger the `click` event on the `summary` element
                // Opera already seems to trigger the `click` event when Enter is pressed
                if (!($.browser.opera && 13 === event.keyCode)) {
                  event.preventDefault();
                  $detailsSummary.click();
                }
              }
            });
      });
    }
  }

  // Return the browser and version that appears to be running. Possible
  // values resemble {fx4, fx35, m1, m11}. Return undefined if the currently
  // running browser can't be identified.
  function detectBrowser() {
    function getVersionGroup(browser, version) {
      if ((browser === undefined) || (version === undefined) || !VERSIONS[browser]) {
        return;
      }

      for (var i = 0; i < VERSIONS[browser].length; i++) {
        if (version < VERSIONS[browser][i][0]) {
          return browser + VERSIONS[browser][i][1];
        }
      }
    }
    return getVersionGroup(BrowserDetect.browser, BrowserDetect.version);
  }

  function initPrepopulatedSlugs() {
    var fields = {
      title: {
        id: '#id_slug',
        dependency_ids: ['#id_title'],
        dependency_list: ['#id_title'],
        maxLength: 50
      }
    };

    $.each(fields, function(i, field) {
      $(field.id).addClass('prepopulated_field');
      $(field.id).data('dependency_list', field.dependency_list)
          .prepopulate($(field.dependency_ids.join(',')),
              field.maxLength);
    });
  }

  function initSummaryCount() {
    var $summaryCount = $('#remaining-characters'),
        $summaryBox = $('#id_summary'),
    // 160 characters is the maximum summary
    // length of a Google result
        warningCount = 160,
        maxCount = $summaryCount.text(),
        updateCount = function() {
          var currentCount = $summaryBox.val().length;
          $summaryCount.text(warningCount - currentCount);
          if(warningCount - currentCount >= 0) {
            $summaryCount.css("color", "black");
          } else {
            $summaryCount.css("color", "red");
            if(currentCount >= maxCount) {
              $summaryBox.val($summaryBox.val().substr(0, maxCount));
            }
          }
        };

    updateCount();
    $summaryBox.bind("input", updateCount);
  }

  /*
   * Initialize the article preview functionality.
   */
  function initArticlePreview() {
    var $preview = $('#preview'),
        $previewBottom = $('#preview-bottom'),
        preview = new k.AjaxPreview($('.btn-preview'), {
          contentElement: $('#id_content'),
          previewElement: $preview
        });
    $(preview).bind('done', function(e, success){
      if (success) {
        $previewBottom.show();
        ShowFor.initForTags();
        $preview.find('select.enable-if-js').removeAttr('disabled');
        $preview.find('.kbox').kbox();
        k.initVideo();
        $('#preview-diff .output').empty();
      }
    });
  }

  // Diff Preview of edits
  function initPreviewDiff() {
    var $diff = $('#preview-diff'),
        $previewBottom = $('#preview-bottom'),
        $diffButton = $('.btn-diff');
    $diff.addClass('diff-this');
    $diffButton.click(function() {
      $diff.find('.to').text($('#id_content').val());
      k.initDiff($diff.parent());
      $previewBottom.show();
      $('#preview').empty()
    });
  }

  function initTitleAndSlugCheck() {
    $('#id_title').change(function() {
      var $this = $(this),
          $form = $this.closest('form'),
          title = $this.val(),
          slug = $('#id_slug').val();
      verifyTitleUnique(title, $form);
      // Check slug too, since it auto-updates and doesn't seem to fire
      // off change event.
      verifySlugUnique(slug, $form);
    });
    $('#id_slug').change(function() {
      var $this = $(this),
          $form = $this.closest('form'),
          slug = $('#id_slug').val();
      verifySlugUnique(slug, $form);
    });

    function verifyTitleUnique(title, $form) {
      var errorMsg = gettext('A document with this title already exists in this locale.');
      verifyUnique('title', title, $('#id_title'), $form, errorMsg);
    }

    function verifySlugUnique(slug, $form) {
      var errorMsg = gettext('A document with this slug already exists in this locale.');
      verifyUnique('slug', slug, $('#id_slug'), $form, errorMsg);
    }

    function verifyUnique(fieldname, value, $field, $form, errorMsg) {
      $field.removeClass('error');
      $field.parent().find('ul.errorlist').remove();
      var data = {};
      data[fieldname] = value;
      $.ajax({
        url: $form.data('json-url'),
        type: 'GET',
        data: data,
        dataType: 'json',
        success: function(json) {
          // Success means we found an existing doc
          var docId = $form.data('document-id');
          if (!docId || (json.id && json.id !== parseInt(docId))) {
            // Collision !!
            $field.addClass('error');
            $field.before(
                $('<ul class="errorlist"><li/></ul>')
                    .find('li').text(errorMsg).end()
            );
          }
        },
        error: function(xhr, error) {
          if(xhr.status === 404) {
            // We are good!!
          } else {
            // Something went wrong, just fallback to server-side
            // validation.
          }
        }
      });
    }
  }

  // If the Customer Care banner is present, animate it and handle closing.
  function initAOABanner() {
    var $banner = $('#banner'),
        cssFrom = { top: -100 },
        cssTo = { top: -10 };
    if ($banner.length > 0) {
      setTimeout(function() {
        $banner
            .css({ display: 'block' })
            .css(cssFrom)
            .animate(cssTo, 500)
            .find('a.close').click(function(e) {
              e.preventDefault();
              $banner.animate(cssFrom, 500, 'swing', function() {
                $banner.css({ display: 'none' });
              });
            });
      }, 500);
    }
  }

  // On document edit/translate/new pages, run validation before opening the
  // submit modal.
  function initPreValidation() {
    var $modal = $('#submit-modal'),
        kbox = $modal.data('kbox');
    kbox.updateOptions({
      preOpen: function() {
        var form = $('.btn-submit').closest('form')[0];
        if (form.checkValidity && !form.checkValidity()) {
          // If form isn't valid, click the modal submit button
          // so the validation error is shown. (I couldn't find a
          // better way to trigger this.)
          $modal.find('button[type="submit"]').click();
          return false;
        }
        // Add this here because the "Submit for Review" button is
        // a submit button that triggers validation and fails
        // because the modal hasn't been displayed yet.
        $modal.find('#id_comment').attr('required', true);
        return true;
      },
      preClose: function() {
        // Remove the required attribute so validation doesn't
        // fail after clicking cancel.
        $modal.find('#id_comment').removeAttr('required');
        return true;
      }
    });
  }

  // The diff revision picker
  function initDiffPicker() {
    $('div.revision-diff').each(function() {
      var $diff = $(this);
      $diff.find('div.picker a').unbind().click(function(ev) {
        ev.preventDefault();
        $.ajax({
          url: $(this).attr('href'),
          type: 'GET',
          dataType: 'html',
          success: function(html) {
            var kbox = new KBox(html, {
              modal: true,
              id: 'diff-picker-kbox',
              closeOnOutClick: true,
              destroy: true,
              title: gettext('Choose revisions to compare')
            });
            kbox.open();
            ajaxifyDiffPicker(kbox.$kbox.find('form'), kbox, $diff);
          },
          error: function() {
            var message = gettext('There was an error.');
            alert(message);
          }
        });
      });
    });
  }

  function ajaxifyDiffPicker($form, kbox, $diff) {
    $form.submit(function(ev) {
      ev.preventDefault();
      $.ajax({
        url: $form.attr('action'),
        type: 'GET',
        data: $form.serialize(),
        dataType: 'html',
        success: function(html) {
          var $container = $diff.parent();
          kbox.close();
          $diff.replaceWith(html);
          initDiffPicker();
          k.initDiff()
        }
      });
    });
  }

  function initReadyForL10n() {
    var $watchDiv = $("#revision-list div.l10n"),
        post_url, checkbox_id;

    $watchDiv.find("a.markasready").click(function() {
      var $check = $(this);
      post_url = $check.data("url");
      checkbox_id = $check.attr("id");
      $("#ready-for-l10n-modal span.revtime").html("("+$check.data("revdate")+")");
    });

    $("#ready-for-l10n-modal input[type=submit], #ready-for-l10n-modal button[type=submit]").click(function() {
      var csrf = $("#ready-for-l10n-modal input[name=csrfmiddlewaretoken]").val(),
          kbox = $("#ready-for-l10n-modal").data("kbox");
      if(post_url != undefined && checkbox_id != undefined) {
        $.ajax({
          type: "POST",
          url: post_url,
          data: {csrfmiddlewaretoken: csrf},
          success: function(response) {
            $("#" + checkbox_id).removeClass("markasready").addClass("yes");
            $("#" + checkbox_id).unbind("click");
            kbox.close();
          },
          error: function() {
            kbox.close();
          }
        });
      }
    });
  }

  function addReferrerAndQueryToVoteForm() {
    // Add the source/referrer and query terms to the helpful vote form
    var urlParams = k.getQueryParamsAsDict(),
        referrer = k.getReferrer(urlParams),
        query = k.getSearchQuery(urlParams, referrer);
    $('.document-vote form')
        .append($('<input type="hidden" name="referrer"/>')
            .attr('value', referrer))
        .append($('<input type="hidden" name="query"/>')
            .attr('value', query));
  }

  function initNeedsChange() {
    // Hide and show the comment box based on the status of the
    // "Needs change" checkbox. Also, make the textarea required
    // when checked.
    var $checkbox = $('#id_needs_change'),
        $comment = $('#document-form li.comment,#approve-modal div.comment');

    if ($checkbox.length > 0) {
      updateComment();
      $checkbox.change(updateComment);
    }

    function updateComment() {
      if ($checkbox.is(':checked')) {
        $comment.slideDown();
        $comment.find('textarea').attr('required', 'required');
      } else {
        $comment.hide();
        $comment.find('textarea').removeAttr('required');
      }
    }
  }

  function watchDiscussion() {
    // For a thread on the all discussions for a locale.
    $('.watch-form').click(function() {
      var form = $(this);
      $.post(form.attr('action'), form.serialize(), function() {
        form.find('.watchtoggle').toggleClass('on')
      }).error(function() {
            // error growl
          });
      return false
    });
  }

  function initEditingTools() {
    // Init the show/hide links for editing tools
    $('#quick-links .edit a').click(function(ev) {
      ev.preventDefault();
      $('#doc-tabs').slideToggle('fast', function() {
        $('body').toggleClass('show-editing-tools');
      });

      if ($(this).is('.show')) {
        $.cookie('show-editing-tools', 1, {path: '/'});
      } else {
        $.cookie('show-editing-tools', null, {path: '/'});
      }
    });
  }

  function initAceEditor() {
    window.highlighting = {};

    var editor = $("<div id='editor'></div>");
    var editor_wrapper = $("<div id='editor_wrapper'></div>");

    var updateHighlightingEditor = function() {
      var session = window.highlighting.session;
      if(!session)
        return;

      var content = $("#id_content").val();
      session.setValue(content);
    };
    window.highlighting.updateEditor = updateHighlightingEditor;

    var switch_link = $("<a></a>")
        .text(gettext("Toggle syntax highlighting"))
        .css({cssFloat: "right", cursor: "pointer"})
        .toggle(function() {
          editor_wrapper.css("display", "none");
          $("#id_content").css("display", "block");
        }, function() {
          updateHighlightingEditor();
          editor_wrapper.css("display", "block");
          $("#id_content").css("display", "none");
        });

    var highlightingEnabled = function() {
      return editor_wrapper.css("display") == 'block';
    };
    window.highlighting.isEnabled = highlightingEnabled;

    editor_wrapper.append(editor);
    $("#id_content").after(switch_link).after(editor_wrapper).hide();

    window.addEventListener("load", function() {
      var ace_editor = ace.edit("editor");
      window.highlighting.editor = ace_editor;
      var session = ace_editor.getSession();
      window.highlighting.session = session;
      session.setMode("ace/mode/sumo");
      session.setUseWrapMode(true);

      $("#id_content").bind("keyup", updateHighlightingEditor);
      updateHighlightingEditor();

      session.on('change', function(e) {
        if(!highlightingEnabled())
          return;
        $("#id_content").val(session.getValue());
      });
    }, false);
  }

  function initFormLock() {
    var $doc = $('#edit-document');
    if (!$doc.length) {
      $doc = $('#localize-document');
    }
    if ($doc.is('.locked')) {
      var $inputs = $doc.find('input:enabled, textarea:enabled')
          .prop('disabled', true);
    }
    $('#unlock-button').on('click', function () {
      $inputs.prop('disabled', false);
      $doc.removeClass('locked');
      $('#locked-warning').slideUp(500);

      var doc_slug = $doc.data('slug');
      var url = window.location.toString();
      // Modify the current url, so we get the right locale.
      url = url.replace(/edit/, 'steal_lock');

      $.ajax({
        url: url
      });
    });
  }

  function initToggleDiff() {
    var $diff = $('#content-diff');
    var $contentOrDiff = $('#content-or-diff');

    if ($diff.length > 0) {
      $contentOrDiff
          .append($diff.clone())
          .append(
              $('<a/>')
                  .text(gettext('Toggle Diff'))
                  .click(function(e) {
                    e.preventDefault();
                    $contentOrDiff.toggleClass('content diff');
                  }));
    }
  }

  function initRevisionList() {
    var $form = $('#revision-list form.filter');
    if(!$form.length) return;

    // This function grabs a fragment from the server and replaces
    // the content of the div with it.
    function updateRevisionList(query) {
      if (query === undefined) {
        query = $form.serialize();
      }
      if (query.charAt(0) !== '?') {
        query = '?' + query;
      }
      var url = $form.attr('action') + query;

      // scroll to the top.
      var scrollPos = Math.min($(document).scrollTop(),
          $('#revision-list').offset().top);
      $(document).scrollTop(scrollPos);
      history.replaceState({}, "", url);
      $('#revisions-fragment').css('opacity', 0);

      $.get(url + '&fragment=1', function(data) {
        $('.loading').hide();
        $('#revisions-fragment').html(data).css('opacity', 1);
      });
    }

    // When the filter form changes, wait a tick and then update.
    var timeout;
    $form.on('change keyup', 'input, select', function() {
      $('.loading').show();
      clearTimeout(timeout);
      timeout = setTimeout(updateRevisionList, 200);
    });

    // Catch page changes, replace with fragment loading.
    $('#revision-list').on('click', '.pagination a', function() {
      var query = $(this)[0].search;
      updateRevisionList(query);
      return false;
    });

    // Treat diff pages as fragments too, and insert them below the current row.
    $('#revision-list').on('click', '.show-diff', function() {
      var $this = $(this);

      $this.hide();
      $this.parent().find('.loading').show();

      var $diffView = $('<div class="diff-view">')
        .hide()
        .appendTo($(this).parents('li').first());

      var url = $this.attr('href');

      $.get(url, function(html) {
        $diffView.html(html);
        // Change the "Edit this diff" button to a "close diff" button.
        $diffView.find('.picker')
          .html('<a href="" class="close-diff">Close diff</a>');
        // show and hide things.
        $diffView.slideDown();
        $this.parent().find('.close-diff').show();
        $this.parent().find('.loading').hide();

        k.initDiff();
      });

      return false;
    });

    // This could be the close diff icon that replaces the open diff icon, or
    // the close diff link inserted into the diff fragment.
    $('#revision-list').on('click', '.close-diff', function() {
      var $row = $(this).parents('li').first();
      $row.find('.diff-view').slideUp(400, function() {
        $row.find('.show-diff').show();
        $row.find('.close-diff').hide();
        $row.find('.diff-view').remove();
      });
      return false;
    });

    // Disable standard form submission
    $form.find('.btn').remove();
    $form.on('keydown', function(e) {
      // 13 is enter.
      if (e.which === 13) {
        return false;
      }
    });

    $form.find('input[type=date]').datepicker();
  }

  $(document).ready(init);

  window.k.makeWikiCollapsable = function() {
    // Hide the TOC
    $('#toc').hide();

    // Make sections collapsable
    $('#doc-content h1').each(function() {
      var $this = $(this);
      var $siblings = $(this).nextAll();

      var sectionElems = [];
      $siblings.each(function() {
        if ($(this).is('h1')) {
          return false;
        }
        sectionElems.push(this);
      });

      var $foldingSection = $('<div />');
      $foldingSection.addClass('wiki-section').addClass('collapsed');
      $this.before($foldingSection);
      $foldingSection.append($this);

      var $section = $('<section />');
      $foldingSection.append($section);

      for (var i=0; i < sectionElems.length; i++) {
        $section.append(sectionElems[i]);
      }
    });

    // Make the header the trigger for toggling state
    $('#doc-content').on('click', 'h1', function() {
      $(this).closest('.wiki-section').toggleClass('collapsed');
    });

    // Uncollapse the first visible one
    $('#doc-content h1:visible').first().click();
  }

  function initExitSupportFor() {
    $('#support-for-exit').live('click', function() {
      $('#support-for').remove();
    });
  }

}(jQuery));

