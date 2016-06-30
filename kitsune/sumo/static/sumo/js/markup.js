/* global jQuery:false, gettext:false, trackEvent:false, KBox:false */
/*
  Marky, the markup toolbar builder

  Usage:
  <script type="text/javascript">
    // Create the simple toolbar (used in Forums and Questions)
    Marky.createSimpleToolbar('#toolbar-container-id', '#textarea-id');

    // or, create the full toolbar (used in the Knowledgebase)
    Marky.createFullToolbar('#toolbar-container-id', '#textarea-id');

    //or, create a custom toolbar.
    Marky.createFullToolbar('#toolbar-container-id', '#textarea-id', [
      new Marky.SimpleButton(
        gettext('Bold'), "'''", "'''", gettext('bold text'),
        'btn-bold'),
      new Marky.SimpleButton(
        gettext('Italic'), "''", "''", gettext('italic text'),
        'btn-italic')
    ]);
  </script>
*/
(function($, gettext, document) {

  var Marky = {
    createSimpleToolbar: function(toolbarSel, textareaSel, options) {
      var defaults = {
        cannedResponses: false,
        privateMessaging: false
      };

      var settings = $.extend({}, defaults, options);

      var SB = Marky.SimpleButton;
      var buttons = [
        new SB(gettext('Bold'), "'''", "'''", gettext('bold text'),
          'btn-bold'),
        new SB(gettext('Italic'), "''", "''", gettext('italic text'),
          'btn-italic'),
        new Marky.Separator(),
        new Marky.LinkButton(),
        new Marky.Separator(),
        new SB(gettext('Numbered List'), '# ', '',
          gettext('Numbered list item'), 'btn-ol', true),
        new SB(gettext('Bulleted List'), '* ', '',
          gettext('Bulleted list item'), 'btn-ul', true)
      ];
      if (settings.mediaButton) {
        buttons.splice(4, 0, new Marky.MediaButton());
      }
      if (settings.cannedResponses) {
        buttons.push(new Marky.Separator(),
          new Marky.CannedResponsesButton());
      }
      if (settings.privateMessaging) {
        buttons.push(new Marky.Separator(),
          new Marky.QuoteButton());
      }

      Marky.createCustomToolbar(toolbarSel, textareaSel, buttons);
    },
    createFullToolbar: function(toolbarSel, textareaSel) {
      var SB = Marky.SimpleButton,
        buttons = Marky.allButtons();
      Marky.createCustomToolbar(toolbarSel, textareaSel, buttons);
    },
    createCustomToolbar: function(toolbarSel, textareaSel, partsArray) {
      var $toolbar = $(toolbarSel || '.editor-tools'),
        textarea = $(textareaSel || '#reply-content, #id_content')[0];
      for (var i = 0, l = partsArray.length; i < l; i++) {
        $toolbar.append(partsArray[i].bind(textarea).node());
      }
    },
    allButtons: function() {
      var SB = Marky.SimpleButton;
      return [
        new SB(gettext('Bold'), "'''", "'''", gettext('bold text'),
          'btn-bold'),
        new SB(gettext('Italic'), "''", "''", gettext('italic text'),
          'btn-italic'),
        new Marky.Separator(),
        new Marky.LinkButton(),
        new Marky.MediaButton(),
        new Marky.Separator(),
        new SB(gettext('Numbered List'), '# ', '',
          gettext('Numbered list item'), 'btn-ol', true),
        new SB(gettext('Bulleted List'), '* ', '',
          gettext('Bulleted list item'), 'btn-ul', true),
        new Marky.Separator(),
        new SB(gettext('Heading 1'), '=', '=', gettext('Heading 1'),
          'btn-h1', true),
        new SB(gettext('Heading 2'), '==', '==', gettext('Heading 2'),
          'btn-h2', true),
        new SB(gettext('Heading 3'), '===', '===', gettext('Heading 3'),
          'btn-h3', true)
      ];
    }
  };


  /*
   * A simple button.
   * Note: `everyline` is a boolean value that says whether or not the selected
   *       text should be broken into multiple lines and have the markup applied
   *       to each line or not. Default is false (do not apply this behavior).
   *       `classes` is a list of classes to include in the output
   */
  Marky.SimpleButton = function(name, openTag, closeTag, defaultText,
                                classes, everyline) {
    this.name = name;
    this.classes = '';
    this.openTag = openTag;
    this.closeTag = closeTag;
    this.defaultText = defaultText;
    this.everyline = everyline;
    if (undefined !== classes) {
      this.classes = classes;
    }

    this.html = '<button class="markup-toolbar-button" />';
  };

  Marky.SimpleButton.prototype = {
    // Binds the button to a textarea (DOM node).
    bind: function(textarea) {
      this.textarea = textarea;
      return this;
    },
    // Renders the html.
    render: function() {
      var $out = $(this.html).attr({
        title: this.name
      }).html(this.name);
      $out.addClass(this.classes);
      return $out;
    },
    // Gets the DOM node for the button.
    node: function() {
      var me = this,
        $btn = this.render();
      $btn.click(function(e) {
        me.handleClick(e);
      });
      return $btn[0];
    },
    // Get selected text
    getSelectedText: function() {
      var selText = '';
      if (window.codemirror && window.highlighting.isEnabled()) {
        var editor = window.highlighting.editor;
        return editor.getSelection();
      }

      if (document.selection && document.selection.createRange) {
        // IE/Opera
        selText = document.selection.createRange().text;
      } else if (this.textarea.selectionStart ||
        parseInt(this.textarea.selectionStart) === 0) {
        // Firefox/Safari/Chrome/etc.
        selText = this.textarea.value.substring(
          this.textarea.selectionStart, this.textarea.selectionEnd);
      }
      return selText;
    },
    // Handles the button click.
    handleClick: function(e) {
      var selText, selStart, selEnd, splitText, range,
        textarea = this.textarea,
        scrollTop = $(textarea).scrollTop(),
        editor = window.highlighting && window.highlighting.editor;

      if (window.codemirror && window.highlighting && window.highlighting.isEnabled()) {
        selText = (editor.somethingSelected()) ? editor.getSelection() : this.defaultText;
        selText = this.openTag + selText + this.closeTag;
        editor.replaceSelection(selText);
        editor.focus();
        e.preventDefault();
        return false;
      }

      textarea.focus();

      if (document.selection && document.selection.createRange) {
        // IE/Opera
        range = document.selection.createRange();
        selText = range.text;
        if (!selText.length) {
          selText = this.defaultText;
        }

        if (this.everyline && -~selText.indexOf('\n')) {
          splitText = this._applyEveryLine(this.openTag, this.closeTag,
            selText);
          range.text = splitText.join('\n');
        } else {
          range.text = this.openTag + selText + this.closeTag;

          if (range.moveStart) {
            range.moveStart('character', (-1 * this.openTag.length) -
              selText.length);
            range.moveEnd('character', (-1 * this.closeTag.length));
          }
        }

        range.select();
      } else if (textarea.selectionStart || parseInt(textarea.selectionStart) === 0) {
        // Firefox/Safari/Chrome/etc.
        selStart = textarea.selectionStart;
        selEnd = textarea.selectionEnd;
        selText = textarea.value.substring(selStart, selEnd);
        if (!selText.length) {
          selText = this.defaultText;
        }

        if (this.everyline && -~selText.indexOf('\n')) {
          splitText = this._applyEveryLine(this.openTag, this.closeTag,
            selText).join('\n');
          textarea.value =
            textarea.value.substring(0, textarea.selectionStart) +
            splitText +
            textarea.value.substring(textarea.selectionEnd);

          textarea.selectionStart = selStart;
          textarea.selectionEnd = textarea.selectionStart +
            splitText.length;
        } else {
          textarea.value =
            textarea.value.substring(0, textarea.selectionStart) +
            this.openTag + selText + this.closeTag +
            textarea.value.substring(textarea.selectionEnd);

          textarea.selectionStart = selStart + this.openTag.length;
          textarea.selectionEnd = textarea.selectionStart +
            selText.length;
        }
      }
      $(textarea).scrollTop(scrollTop);
      e.preventDefault();
      return false;
    },
    _applyEveryLine: function(opentag, closetag, block) {
      return $.map(block.split('\n'), function(line) {
        return (line.replace(/\s+/, '').length ?
          opentag + line + closetag : line);
      });
    }
  };

  /*
   * A button separator.
   */
  Marky.Separator = function() {
    this.html = '<span class="separator"></span>';
  };

  Marky.Separator.prototype = {
    node: function() {
      return $(this.html)[0];
    },
    bind: function() {
      return this;
    }
  };

  /*
   * The link helper.
   */
  Marky.LinkButton = function() {
    this.name = gettext('Insert a link...');
    this.classes = 'btn-link';
    this.openTag = '[http://example.com ';
    this.closeTag = ']';
    this.defaultText = gettext('link text');
    this.everyline = false;

    this.origOpenTag = this.openTag;
    this.origCloseTag = this.closeTag;
    this.origDefaultText = this.defaultText;

    this.html = '<button class="markup-toolbar-button" />';
  };

  Marky.LinkButton.prototype = $.extend({}, Marky.SimpleButton.prototype, {
    // Gets the DOM node for the button.
    node: function() {
      var me = this,
        $btn = this.render();
      $btn.click(function(e) {
        me.openModal(e);
      });
      return $btn[0];
    },
    reset: function() {
      this.openTag = this.origOpenTag;
      this.closeTag = this.origCloseTag;
      this.defaultText = this.origDefaultText;
    },
    openModal: function(ev) {
      var me = this,
      // TODO: look at using a js template solution (jquery-tmpl?)
        $html = $(
            '<section class="marky">' +
            '<label>' + gettext('Link text:') + '</label>' +
            '<input type="text" name="link-text" />' +
            '<label>' + gettext('Link target:') + '</label>' +
            '<ol><li><label><input type="radio" name="link-type" value="internal" /> ' +
            gettext('Support article:') + '</label> ' +
            '<input type="text" name="internal" placeholder="' +
            gettext('Enter the name of the article') + '" /></li>' +
            '<li><label><input type="radio" name="link-type" value="external" /> ' +
            gettext('External link:') + '</label> ' +
            '<input type="text" name="external" placeholder="' +
            gettext('Enter the URL of the external link') + '" /></li>' +
            '</ol><div class="submit"><button type="button" class="btn btn-important"></button>' +
            '<a href="#cancel" class="kbox-cancel">' + gettext('Cancel') +
            '</a></div></section>' // whew, yuck!?
        ),
        selectedText = me.getSelectedText(),
        kbox;

      $html.find('li input[type="text"]').focus(function() {
        $(this).closest('li').find('input[type="radio"]').click();
      });

      // Perform a query for the sections of an article if
      // last character is a pound:
      var performSectionSearch = function(request) {
        return (request.term.indexOf('#') === request.term.length - 1);
      };

      var results = [];

      // Get the article URL by providing the article name:
      var getArticleURL = function(name) {
        for (var i = 0; i < results.length; i++) {
          if (name === results[i].label) {
            return results[i].url;
          }
        }

        return null;
      };

      var articleSearch = function(request, response) {
        results = [];
        $.ajax({
          url: '/en-US/search',
          data: {
            format: 'json',
            q: request.term,
            a: 1,
            w: 1,
            language: $('html').attr('lang')
          },
          dataType: 'json',
          success: function(data, textStatus) {
            $.map(data.results, function(val, i) {
              results.push({
                label: val.title,
                url: val.url
              });
            });
            response(results);
          }
        });
      };

      var sectionSearch = function(request, response) {
        var articleName = request.term.split('#')[0];
        var articleURL = getArticleURL(articleName);

        if (!articleURL) {
          return;
        }

        $.ajax({
          url: articleURL,
          dataType: 'text',
          success: function(data, status) {
            var headings = $("[id^='w_']", data);
            var array = [];

            if (headings.length === 0) {
              array.push({
                label: gettext('No sections found'),
                value: request.term.replace('#', ''),
                target: ''
              });
            }

            headings.each(function() {
              var element = this.nodeName;
              var level = element.substring(1);
              var label = $(this).text();
              var target = $(this).attr('id');
              var value = request.term + target;

              array.push({
                label: label,
                value: value,
                target: target
              });
            });
            response(array);
          }
        });
      };

      $html.find('input[name="internal"]').autocomplete({
        source: function(request, response) {
          if (performSectionSearch(request)) {
            sectionSearch(request, response);
          } else {
            articleSearch(request, response);
          }
        },
        select: function(event, ui) {
          if (!ui.item.target) {
            return;
          }

          var $linktext = $html.find('input[name=link-text]');
          if ($linktext.val() === '') {
            $linktext.val(ui.item.label);
          }
        }
      });

      $html.find('button').text(gettext('Insert Link')).click(function(e) {
        // Generate the wiki markup based on what the user has selected
        // (interval vs external links) and entered into the textboxes,
        // if anything.
        var val = $html.find('input[type="radio"]:checked').val(),
          text = $html.find('input[name=link-text]').val(),
          $internal = $html.find('input[name="internal"]'),
          $external = $html.find('input[name="external"]');
        me.reset();
        if (val === 'internal') {
          var title = $internal.val();
          if (title) {
            if (title === selectedText) {
              // The title wasn't changed, so lets keep it selected.
              me.openTag = '[[';
              me.closeTag = ']]';
              if (text) {
                me.closeTag = '|' + text + me.closeTag;
              }
            } else {
              // The title changed, so lets insert link before the cursor.
              me.openTag = '[[' + title;
              if (text) {
                me.openTag += '|' + text;
              }
              me.openTag += ']] ';
              me.closeTag = '';
              me.defaultText = '';
            }
          } else {
            me.openTag = '[[';
            me.closeTag = ']]';
            if (text) {
              me.closeTag = '|' + text + ']]';
            }
            me.defaultText = gettext('Knowledge Base Article');
          }
        } else {
          var link = $external.val();
          if (link) {
            if (link.indexOf('http') !== 0) {
              link = 'http://' + link;
            }
            me.openTag = '[' + link + ' ';
            if (text) {
              me.openTag += text + '] ';
              me.closeTag = '';
              me.defaultText = '';
            }
          } else if (text) {
            me.defaultText = text;
          }
        }

        me.handleClick(e);
        kbox.close();
      });

      if (selectedText) {
        // If there user has selected text, lets default to it being
        // the Article Title.
        $html.find('input[name="internal"]').val(selectedText).focus();
      }

      kbox = new KBox($html, {
        title: this.name,
        destroy: true,
        modal: true,
        id: 'link-modal',
        container: $('body')
      });
      kbox.open();

      ev.preventDefault();
      return false;
    }
  });

  /*
   * The media helper.
   */
  Marky.MediaButton = function() {
    this.name = gettext('Insert media...');
    this.classes = 'btn-media';
    this.openTag = '';
    this.closeTag = '';
    this.defaultText = gettext('media');
    this.everyline = false;

    this.html = '<button class="markup-toolbar-button" />';
  };

  Marky.MediaButton.prototype = $.extend({}, Marky.SimpleButton.prototype, {
    // Gets the DOM node for the button.
    node: function() {
      var me = this,
        $btn = this.render();
      $btn.click(function(e) {
        me.openModal(e);
      });
      return $btn[0];
    },
    reset: function() {
      this.openTag = '';
      this.closeTag = '';
      this.defaultText = '';
    },
    openModal: function(ev) {
      var me = this,
        $editor = $(me.textarea).closest('.editor'),
        mediaSearchUrl = $editor.data('media-search-url'),
        galleryUrl = $editor.data('media-gallery-url'),
      // TODO: look at using a js template solution (jquery-tmpl?)
        $html = $(
            '<section class="marky">' +
            '<div class="filter cf">' +
            '<form class="simple-search-form" id="gallery-modal-search"><input type="text" name="q" class="searchbox"' +
            'placeholder="' + gettext('Search Gallery') + '" />' +
            '<button type="submit" class="submit-button" title="' + gettext('Search Gallery') + '">' +
            gettext('Search Gallery') + '</button></form>' +
            '<div class="type">' +
            '<span>' + gettext('Show:') + '</span>' +
            '<ol><li data-type="image" class="selected">' + gettext('Images') + '</li>' +
            '<li data-type="video">' + gettext('Videos') + '</li></ol></div>' +
            '<div class="locale-filter">' + gettext('Show media for:') + ' <select /></div></div>' +
            '<div class="placeholder" /><div class="submit">' +
            '<button class="btn btn-important">' + gettext('Insert Media') + '</button>' +
            '<a href="' + galleryUrl + '#upload" class="upload" target="_blank">' +
            gettext('Upload Media') + '</a>' +
            '<a href="#cancel" class="kbox-cancel">' + gettext('Cancel') + '</a></div>' +
            '</section>'
        ),
        selectedText = me.getSelectedText(),
        mediaType = $html.find('div.type li.selected').data('type'),
        mediaQ = '',
        mediaLocale = $('html').attr('lang'),
        mediaPage = 1,
        kbox;

      // Handle Images/Videos filter
      $html.find('div.type li').click(function(e) {
        var $this = $(this);
        if (!$this.is('.selected')) {
          $html.find('div.type li.selected').removeClass('selected');
          $this.addClass('selected');
          mediaType = $this.data('type');
          mediaPage = 1;
          updateResults();
        }
        e.preventDefault();
        return false;
      });

      // Handle locale filter
      var $lf = $html.find('div.locale-filter select');
      $lf.html($('#_languages-select-box').html());
      $lf.on('change', function() {
        mediaPage = 1;
        mediaLocale = $(this).val();
        updateResults();
      });

      // Handle Search
      $html.find('form#gallery-modal-search').submit(function(e) {
        mediaQ = $html.find('input[name="q"]').val();
        mediaPage = 1;
        updateResults();
        e.preventDefault();
        return false;
      });

      // Handle Upload link
      $html.find('a.upload').click(function(e) {
        // Close the modal. The link itself will open gallery in new tab/window.
        kbox.close();
      });

      // Handle pagination
      $html.delegate('ol.pagination a', 'click', function(e) {
        mediaPage = parseInt($(this).attr('href').split('&page=')[1], 10);
        updateResults();
        e.preventDefault();
        return false;
      });

      // Handle 'Insert Media' button click
      $html.find('div.submit button').click(function(e) {
        // Generate the wiki markup based on what the user has selected.
        me.reset();

        var $selected = $html.find('#media-list > li.selected');
        if ($selected.length < 1) {
          alert(gettext('Please select an image or video to insert.')); // eslint-disable-line
          return false;
        }

        me.openTag = '[[';
        me.openTag += (mediaType === 'image') ? 'Image' : 'Video';
        me.openTag += ':' + $selected.find('a').attr('title') + ']] ';

        me.handleClick(e);
        kbox.close();
      });

      updateResults();

      // Update the media list via ajax call.
      function updateResults(type, q) {
        $html.addClass('processing');
        $.ajax({
          url: mediaSearchUrl,
          type: 'GET',
          data: {type: mediaType, q: mediaQ, page: mediaPage,
            locale: mediaLocale},
          dataType: 'html',
          success: function(html) {
            $html.find('div.placeholder').html(html);
            $html.find('#media-list > li').click(function(e) {
              var $this = $(this),
                $mediaList = $(this).parent();
              $mediaList.find('li.selected').removeClass('selected');
              $this.addClass('selected');
              e.preventDefault();
              return false;
            });
          },
          error: function() {
            var message = gettext('Oops, there was an error.');
            $html.find('div.placeholder').html('<div class="msg">' +
              message + '</div>');
          },
          complete: function() {
            $html.removeClass('processing');
          }
        });
      }

      kbox = new KBox($html, {
        title: this.name,
        destroy: true,
        modal: true,
        id: 'media-modal',
        container: $('body'),
        position: 'none'
      });
      kbox.open();

      ev.preventDefault();
      return false;
    }
  });

  /*
   * The canned responses helper
   */
  Marky.CannedResponsesButton = function() {
    this.name = gettext('Common responses');
    this.classes = 'btn-cannedresponses';
    this.openTag = '';
    this.closeTag = '';
    this.defaultText = gettext('cannedresponses');
    this.everyline = false;

    this.html = '<a class="markup-toolbar-link" href="#"/>';
  };

  Marky.CannedResponsesButton.prototype = $.extend({}, Marky.SimpleButton.prototype, {
    // Gets the DOM node for the button.
    node: function() {
      var me = this,
        $btn = this.render();
      $btn.click(function(e) {
        me.openModal(e);
      });

      me.getPermissionBits();

      return $btn[0];
    },
    reset: function() {
      this.openTag = '';
      this.closeTag = '';
      this.defaultText = '';
    },
    openModal: function(e) {
      var me = this,
        $editor = $(me.textarea).closest('.editor'),
      // TODO: look at using a js template solution (jquery-tmpl?)
        $html = $(
            '<section class="marky">' +
            '<div class="search simple-search-form">' +
            '<input type="text" name="q" id="filter-responses-field" placeholder="' +
            gettext('Search for common responses') + '" class="searchbox"/>' +
            '</div></div>' +
            '<div class="area">' +
            '<div id="responses-area">' +
            '<h2 class="heading-label">' + gettext('Categories') + '</h2>' +
            '<ul class="category-list sidebar-nav">' +
            '<li class="status-indicator busy">' + gettext('Loading...') + '</li>' +
            '</ul></div>' +
            '<div id="response-list-area">' +
            '<h2 class="heading-label">' + gettext('Responses') + '</h2>' +
            '<h4 class="nocat-label">' + gettext('Please select a category from the previous column or start a search.') + '</h4>' +
            '<p class="response-list"/>' +
            '</div>' +
            '<div id="response-content-area">' +
            '<h2 class="heading-label preview-label">' + gettext('Response editor') + '</h2>' +
            '<button class="toggle-view btn">' + gettext('Switch to preview mode') + '</button>' +
            '<p class="response-preview">' +
            '<textarea id="response-content">' +
            '</textarea></p>' +
            '<p class="response-preview-rendered"></p>' +
            '</div>' +
            '</div>' +
            '</div>' +
            '<div class="placeholder" /><div class="submit" id="response-submit-area">' +
            '<button id="insert-response" class="btn btn-important">' + gettext('Insert Response') + '</button>' +
            '<a href="#cancel" class="kbox-cancel">' + gettext('Cancel') + '</a>' +
            '</div>' +
            '</section>'
        ),
        selectedText = me.getSelectedText(),
        kbox;

      var cannedResponsesUrl = '/kb/common-forum-responses';
      var previewUrl = 'answer-preview-async';

      function updatePreview() {
        var response = $('#response-content').val();
        var token = $('[name=csrfmiddlewaretoken]').attr('value');

        toggleThrobber(true);

        $.ajax({
          type: 'POST',
          url: previewUrl,
          data: {
            content: response,
            csrfmiddlewaretoken: token
          },
          dataType: 'html',
          success: function(html) {
            var $container = $('.response-preview-rendered');
            var $response_preview = $(html).find('.main-content');
            $container.html($response_preview);
          },
          complete: function() {
            toggleThrobber(false);
          }
        });
      }

      function getContent(articleUrl) {
        // If the article doesn't exist, it has /new in its URL
        // Don't query nonexisting articles
        if (!articleUrl || articleUrl.indexOf('/new') !== -1) {
          return;
        }

        toggleThrobber(true);

        $.ajax({
          url: articleUrl + '/edit',
          dataType: 'html',
          success: function(data, status) {
            var article_src = $('#id_content', data).val();
            var $textbox = $('#response-content');
            $textbox.val(article_src);
            $textbox.data('slug', articleUrl);
            updatePreview();
          },
          complete: function() {
            toggleThrobber(false);
          }
        });
      }

      function toggleThrobber(busy) {
        var $label = $('.preview-label');
        if (busy) {
          $label.addClass('busy');
        } else {
          $label.removeClass('busy');
        }
      }

      function isAllowedToUseResponse(response_target) {
        if (response_target.indexOf('#') === -1) {
          // No permission markers: Everyone's allowed
          return true;
        }

        var articleUrl = response_target.split('#')[0];
        var permBits = response_target.split('#')[1];
        response_target = articleUrl;

        for (var i = 0; i < permBits.length; i++) {
          var bit = permBits[i];
          if (me.permissionBits.indexOf(bit) !== -1) {
            return true;
          }
        }
        return false;
      }

      function insertResponse() {
        var sourceContent = $('#response-content').val();
        var slug = $('#response-content').data('slug');
        var $responseTextbox = $('#id_content');
        var targetContent = $responseTextbox.val();

        trackEvent('Canned response usage', slug);

        $responseTextbox.val(targetContent + sourceContent);
      }

      function searchResponses(term) {
        term = term.toLowerCase().trim();
        var $searchHeading = $html.find('#response-list-area .heading-label');
        var $noCategorySelected = $html.find('.nocat-label');
        var $responseLists = $html.find('.response-list ul');
        var $responses = $html.find('.response');
        var $responseListArea = $html.find('#response-list-area');
        var $responsesArea = $html.find('#responses-area');

        if (term === '') {
          $searchHeading.text(gettext('Responses'));
          $responseListArea.removeClass('filtered');
          $responsesArea.removeClass('filtered');
          $noCategorySelected.show();
          $responses.show();
          $responseLists.hide();
          return;
        }

        $responseListArea.addClass('filtered');
        $responsesArea.addClass('filtered');
        $searchHeading.text(gettext('Matching responses'));
        $noCategorySelected.hide();
        $responseLists.show();

        $responses.each(function() {
          var text = $(this).text().toLowerCase();
          if (text.indexOf(term) === -1) {
            $(this).hide();
          } else {
            $(this).show();
          }
        });
      }

      function loadCannedResponses() {
        var siteLanguage = window.location.pathname.split('/')[1];
        var targetUrl = '/' + siteLanguage + cannedResponsesUrl;

        $.ajax({
          url: targetUrl,
          type: 'GET',
          dataType: 'html',
          success: function(html) {
            var $categoryList = $('.category-list'),
              $responsesList = $('.response-list'),
              $categories = $(html).find('[id^=w_]');

            $categoryList.empty();
            $responsesList.empty();

            $categories.each(function() {
              var label = $(this).text(),
                $headingItem = $(document.createElement('li')),
                $responses = $(document.createElement('ul')).addClass('sidebar-nav').hide(),
                $catResponses = $(this).nextUntil('[id^=w_]').find('a'),
                $noCatLabel = $html.find('.nocat-label'),
                $otherResponses,
                $otherHeadings;

              $catResponses.each(function() {
                var $response = $(document.createElement('li')).addClass('response').text($(this).text());
                var response_target = $(this).attr('href');
                var canUseResponse = isAllowedToUseResponse(response_target);
                response_target = response_target.split('#')[0];

                if (canUseResponse) {
                  $response.click(function() {
                    $('.response-list li').not($(this)).removeClass('selected');
                    $(this).addClass('selected');
                    getContent(response_target);
                  });

                  $responses.append($response);
                }
              });

              $headingItem.addClass('response-heading').text(label)
                .on('click', function() {
                  $noCatLabel.hide();
                  $otherResponses = $responsesList.find('ul').not($responses);
                  $otherResponses.hide();

                  $otherHeadings = $categoryList.find('.response-heading').not($headingItem);
                  $otherHeadings.removeClass('selected');

                  $(this).addClass('selected');
                  $responses.show();
                });

              $categoryList.append($headingItem);
              $responsesList.append($responses);
            });
          },
          error: function() {
            var statusIndicator = $('.status-indicator');
            statusIndicator.removeClass('busy');
            statusIndicator.text(gettext('There was an error checking for canned responses.'));
          }
        });

        // return true so that the kbox actually opens:
        return true;
      }

      kbox = new KBox($html, {
        title: this.name,
        destroy: true,
        modal: true,
        id: 'media-modal',
        container: $('body'),
        position: 'none',
        preOpen: loadCannedResponses
      });

      kbox.open();

      $html.find('#insert-response').click(function() {
        insertResponse();
        kbox.close();
      });

      $html.find('#filter-responses-field').keyup(function() {
        var term = $(this).val();
        searchResponses(term);
      });

      var $previewLabel = $html.find('.preview-label');
      var $contentArea = $html.find('.response-preview');
      var $renderedPreview = $html.find('.response-preview-rendered');

      $html.find('.toggle-view').toggle(
        function() {
          updatePreview();
          $previewLabel.text(gettext('Response preview'));
          $(this).text(gettext('Switch to edit mode'));

          $contentArea.hide();
          $renderedPreview.show();
        },
        function() {
          $previewLabel.text(gettext('Response editor'));
          $(this).text(gettext('Switch to preview mode'));

          $contentArea.show();
          $renderedPreview.hide();
        });

      e.preventDefault();
      return false;
    },

    permissionBits: [],

    getPermissionBits: function() {
      var profile_link = $('#aux-nav .user').attr('href'),
        me = this;
      if (!profile_link || profile_link === '') {
        return;
      }

      $.ajax({
        url: profile_link,
        dataType: 'html',
        success: function(data, status) {
          var userGroups = $('#groups li', data);
          userGroups.each(function() {
            var group = $(this).text();

            // Contributors:
            if (group === 'Contributors') {
              me.permissionBits.push('c');
            }

            // Moderators:
            if (group === 'Forum Moderators') {
              me.permissionBits.push('m');
            }

            // Administrators:
            if (group === 'Administrators') {
              me.permissionBits.push('a');
            }
          });
        }
      });
    }
  });

  /*
   * The quote button helper
   */
  Marky.QuoteButton = function() {
    var name = gettext('Quote previous message...');
    var previousContent = $('#read-message').attr('data-message-content');
    var previousAuthor = $('.from a').text();
    var previousAuthorLink = $('.from a').attr('href');
    var quote = '[' + previousAuthorLink + ' ' + previousAuthor + '] ' +
      gettext('said') + '\r\n';
    quote += '<blockquote>\r\n';
    quote += previousContent + '\r\n';
    quote += '</blockquote>\r\n';

    return new Marky.SimpleButton(name, quote, '', '', 'btn-quote', true);
  };

  window.Marky = Marky;

})(jQuery, gettext, document);
