import "jquery-ui/ui/widgets/autocomplete";
import trackEvent from "sumo/js/analytics";
import KBox from "sumo/js/kbox";

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
      new Marky.MarkupButton(
        gettext('Bold'), "'''", "'''", gettext('bold text'),
        'btn-bold'),
      new Marky.MarkupButton(
        gettext('Italic'), "''", "''", gettext('italic text'),
        'btn-italic')
    ]);
  </script>
*/

var Marky = {
  createSimpleToolbar: function(toolbarSel, textareaSel, options) {
    var defaults = {
      cannedResponses: false,
      privateMessaging: false
    };

    var settings = $.extend({}, defaults, options);

    var MB = Marky.MarkupButton;
    var buttons = [
      new MB(gettext('Bold'), "'''", "'''", gettext('bold text'),
        'btn-bold'),
      new MB(gettext('Italic'), "''", "''", gettext('italic text'),
        'btn-italic'),
      new Marky.Separator(),
      new Marky.LinkButton(),
      new Marky.Separator(),
      new MB(gettext('Numbered List'), '# ', '',
        gettext('Numbered list item'), 'btn-ol', true),
      new MB(gettext('Bulleted List'), '* ', '',
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
    var buttons = Marky.allButtons();
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
    var MB = Marky.MarkupButton;
    return [
      new MB(gettext('Bold'), "'''", "'''", gettext('bold text'),
        'btn-bold'),
      new MB(gettext('Italic'), "''", "''", gettext('italic text'),
        'btn-italic'),
      new Marky.Separator(),
      new Marky.LinkButton(),
      new Marky.MediaButton(),
      new Marky.Separator(),
      new MB(gettext('Numbered List'), '# ', '',
        gettext('Numbered list item'), 'btn-ol', true),
      new MB(gettext('Bulleted List'), '* ', '',
        gettext('Bulleted list item'), 'btn-ul', true),
      new Marky.Separator(),
      new MB(gettext('Heading 1'), '=', '=', gettext('Heading 1'),
        'btn-h1', true),
      new MB(gettext('Heading 2'), '==', '==', gettext('Heading 2'),
        'btn-h2', true),
      new MB(gettext('Heading 3'), '===', '===', gettext('Heading 3'),
        'btn-h3', true)
    ];
  }
};


/**
 * A simple button template. Do not use directly:
 * use MarkupButton or InsertButton instead.
 */
class SimpleButton {
  /**
   * @param {string} name - Button title.
   * @param {string} classes - A list of classes to include in the output.
   */
  constructor(name, classes = '') {
    this.name = name;
    this.classes = classes;

    this.html = '<button class="markup-toolbar-button" type="button" />';
  }

  /**
   * Binds the button to a textarea (DOM node).
   */
  bind(textarea) {
    this.textarea = textarea;
    return this;
  }

  /**
   * Renders the html.
   */
  render() {
    const $out = $(this.html)
      .attr({
        title: this.name,
      })
      .html(this.name);
    $out.addClass(this.classes);
    return $out;
  }

  /**
   * Get selected text
   */
  getSelectedText() {
    if (window.codemirror && window.highlighting.isEnabled()) {
      const editor = window.highlighting.editor;
      return editor.getSelection();
    }

    if (typeof this.textarea.selectionStart === 'number') {
      return this.textarea.value.substring(
        this.textarea.selectionStart,
        this.textarea.selectionEnd,
      );
    }
    return '';
  }
}

/**
 * A button that wraps the selected text in markup.
 */
class MarkupButton extends SimpleButton {
  /**
   * @param {string} name - Button title.
   * @param {string} openTag - Markup placed before the selected text.
   * @param {string} closeTag - Markup placed after the selected text.
   * @param {string} defaultText - Default text used when no text is selected.
   * @param {string} classes - A list of classes to include in the output.
   * @param {boolean} everyline - Says whether or not the selected
   *   text should be broken into multiple lines and have the markup applied
   *   to each line or not. Default is false (do not apply this behavior).
   */
  constructor(name, openTag, closeTag, defaultText, classes = '', everyline) {
    super(name, classes);

    this.openTag = openTag;
    this.closeTag = closeTag;
    this.defaultText = defaultText;
    this.everyline = everyline;
  }

  /**
   * Gets the DOM node for the button.
   */
  node() {
    const me = this,
      $btn = this.render();
    $btn.on('click', function (e) {
      me.handleClick(e);
    });
    return $btn[0];
  }

  /**
   * Handles the button click.
   */
  handleClick(e) {
    const me = this,
      textarea = this.textarea,
      scrollTop = $(textarea).scrollTop();

    function configureSelection(selText) {
      const applyEveryLine = me.everyline && selText.includes('\n');
      me.markup = applyEveryLine
        ? me.#applyEveryLine(selText).join('\n')
        : me.openTag + selText + me.closeTag;

      me.selStartDiff = applyEveryLine ? 0 : me.openTag.length;
      me.selLength = applyEveryLine ? me.markup.length : selText.length;
    }

    if (window.codemirror && window.highlighting && window.highlighting.isEnabled()) {
      const editor = window.highlighting.editor;
      const selText = (editor.somethingSelected()) ? editor.getSelection() : this.defaultText;
      const fromIndex = editor.indexFromPos(editor.getCursor('from'));

      configureSelection(selText);
      editor.replaceSelection(this.markup);
      editor.setSelection(
        editor.posFromIndex(fromIndex + this.selStartDiff),
        editor.posFromIndex(fromIndex + this.selStartDiff + this.selLength),
      );

      editor.focus();
      e.preventDefault();
      return false;
    }

    textarea.focus();

    if (typeof textarea.selectionStart === 'number') {
      const selStart = textarea.selectionStart;
      const selEnd = textarea.selectionEnd;
      const selText = textarea.value.substring(selStart, selEnd) || this.defaultText;

      configureSelection(selText);
      textarea.value =
        textarea.value.substring(0, textarea.selectionStart) +
        this.markup +
        textarea.value.substring(textarea.selectionEnd);
      textarea.selectionStart = selStart + this.selStartDiff;
      textarea.selectionEnd = textarea.selectionStart + this.selLength;
    }

    $(textarea).scrollTop(scrollTop);
    e.preventDefault();
    return false;
  }

  /**
   * Wraps each line of the given text block in markup.
   * @param {string} block - Text block to be wrapped in markup.
   * @returns {string[]} - Array of lines, each wrapped in markup.
   */
  #applyEveryLine(block) {
    return $.map(block.split('\n'), (line) =>
      line.trim().length ? this.openTag + line + this.closeTag : line,
    );
  }
}

/**
 * A button that inserts customized markup, replacing the selected text.
 * Child classes must implement `openModal(event)`.
 */
class InsertButton extends SimpleButton {
  /**
   * @param {string} name - Button title.
   * @param {markup} markup - Markup to be inserted, replacing the selected text.
   * @param {string} classes - A list of classes to include in the output.
   */
  constructor(name, markup, classes = '') {
    super(name, classes);

    this.markup = markup;
    this.origMarkup = this.markup;
  }

  /**
   * Resets markup.
   */
  reset() {
    this.markup = this.origMarkup;
  }

  /**
   * Gets the DOM node for the button.
   */
  node() {
    const me = this,
      $btn = this.render();
    $btn.on('click', function (e) {
      me.openModal(e);
    });
    return $btn[0];
  }

  /**
   * Handles the button click.
   */
  handleClick(e) {
    const textarea = this.textarea,
      scrollTop = $(textarea).scrollTop();

    if (window.codemirror && window.highlighting && window.highlighting.isEnabled()) {
      const editor = window.highlighting.editor;
      editor.replaceSelection(this.markup);
      editor.focus();
      e.preventDefault();
      return false;
    }

    textarea.focus();

    if (typeof textarea.selectionStart === 'number') {
      const selStart = textarea.selectionStart;
      const selEnd = textarea.selectionEnd;

      textarea.value =
        textarea.value.substring(0, textarea.selectionStart) +
        this.markup +
        textarea.value.substring(textarea.selectionEnd);

      textarea.selectionStart = selStart + this.markup.length;
      textarea.selectionEnd = textarea.selectionStart;
    }

    $(textarea).scrollTop(scrollTop);
    e.preventDefault();
    return false;
  }
}

/**
 * A button separator.
 */
class Separator {
  constructor() {
    this.html = '<span class="separator"></span>';
  }

  node() {
    return $(this.html)[0];
  }

  bind() {
    return this;
  }
}

/**
 * The link helper.
 */
class LinkButton extends InsertButton {
  constructor() {
    super(gettext('Insert a link...'), '', 'btn-link');
  }

  openModal(ev) {
    const me = this,
      // TODO: look at using a js template solution (jquery-tmpl?)
      $html = $(
        '<form class="marky">' +
        '<div class="field">' +
        '<label>' + gettext('Link text:') + '</label>' +
        '<input type="text" name="link-text" autocomplete="off" />' +
        '</div>' +
        '<div class="field">' +
        '<label>' + gettext('Link target:') + '</label>' +
        '<ol><li class="field"><div class="field radio is-condensed"><input type="radio" name="link-type" id="id_link-type-internal" value="internal" /><label for="id_link-type-internal">' +
        gettext('Support article:') + '</label></div>' +
        '<input type="text" name="internal" placeholder="' +
        gettext('Enter the name of the article') + '" /></li>' +
        '<li class="field"><div class="field radio is-condensed"><input type="radio" name="link-type" id="id_link-type-external" value="external" /><label for="id_link-type-external">' +
        gettext('External link:') + '</label></div>' +
        '<input type="text" name="external" placeholder="' +
        gettext('Enter the URL of the external link') + '" autocomplete="off" /></li>' +
        '</ol></div><div class="submit sumo-button-wrap align-full reverse-on-desktop"><button type="submit" class="sumo-button primary-button">' + gettext('Insert Link') + '</button>' +
        '<a href="#cancel" class="kbox-cancel sumo-button secondary-button">' + gettext('Cancel') +
        '</a></div></form>' // whew, yuck!?
      );

    const $linkText = $html.find('input[name="link-text"]');
    const $internal = $html.find('input[name="internal"]');
    const $external = $html.find('input[name="external"]');
    const $submitButton = $html.find('button[type="submit"]');

    $html.find('li input[type="text"]').on('focus', function () {
      $(this).closest('li').find('input[type="radio"]').trigger('click');
    });

    // Make the text input of the selected link-type radio required.
    function updateRequiredTarget() {
      const val = $html.find('input[name="link-type"]:checked').val();

      $internal.prop('required', val === 'internal');
      $external.prop('required', val === 'external');
    }

    $html.find('input[name="link-type"]').prop('required', true);
    $html.find('input[name="link-type"]').on('change', updateRequiredTarget);

    // Disable the Submit button while the form is invalid.
    function updateSubmitButton() {
      $submitButton.prop('disabled', !$html[0].checkValidity());
    }

    $html.find('li input[type="text"]').on('change', updateSubmitButton);
    $html.find('input[name="link-type"]').on('change', updateSubmitButton);

    // Perform a query for the sections of an article if
    // last character is a pound:
    function performSectionSearch(request) {
      return request.term.endsWith('#');
    }

    let results = [];

    // Get the article URL by providing the article name:
    function getArticleURL(name) {
      for (let i = 0; i < results.length; i++) {
        if (name === results[i].label) {
          return results[i].url;
        }
      }

      return null;
    }

    function articleSearch(request, response) {
      results = [];
      $.ajax({
        url: '/en-US/search',
        data: {
          format: 'json',
          q: request.term,
          a: 1,
          w: 1,
          language: $('html').attr('lang'),
        },
        dataType: 'json',
        success: function (data, textStatus) {
          $.map(data.results, function (val, i) {
            results.push({
              label: val.title,
              url: val.url,
            });
          });
          response(results);
        },
      });
    }

    function sectionSearch(request, response) {
      var articleName = request.term.split('#')[0];
      var articleURL = getArticleURL(articleName);

      if (!articleURL) {
        return;
      }

      $.ajax({
        url: articleURL,
        dataType: 'text',
        success: function (data, status) {
          const headings = $("[id^='w_']", data);
          const array = [];

          if (headings.length === 0) {
            array.push({
              label: gettext('No sections found'),
              value: request.term.replace('#', ''),
              target: '',
            });
          }

          headings.each(function () {
            const label = $(this).text();
            const target = $(this).attr('id');
            const value = request.term + target;

            array.push({
              label: label,
              value: value,
              target: target,
            });
          });
          response(array);
        },
      });
    }

    $internal.autocomplete({
      source: function (request, response) {
        if (performSectionSearch(request)) {
          sectionSearch(request, response);
        } else {
          articleSearch(request, response);
        }
      },
      select: function (event, ui) {
        if (!ui.item.target) {
          return;
        }

        if ($linkText.val() === '') {
          $linkText.val(ui.item.label);
        }
      },
    });

    $html.on('submit', function (e) {
      // Generate the wiki markup based on what the user has selected
      // (interval vs external links) and entered into the textboxes,
      // if anything.
      e.preventDefault();

      const val = $html.find('input[type="radio"]:checked').val(),
        text = $html.find('input[name=link-text]').val();

      me.reset();
      if (val === 'internal') {
        const title = $internal.val() || gettext('Knowledge Base Article');
        if (!text || title === text) {
          me.markup = '[[' + title + ']]';
        } else {
          me.markup = '[[' + title + '|' + text + ']]';
        }
      } else {
        let link = $external.val() || 'https://example.com';
        if (link.indexOf('http') !== 0) {
          link = 'http://' + link;
        }
        if (!text) {
          me.markup = '[' + link + ']';
        } else {
          me.markup = '[' + link + ' ' + text + ']';
        }
      }

      me.handleClick(e);
      kbox.close();
    });

    const selectedText = me.getSelectedText();
    if (selectedText) {
      // If there is selected text, make it the link text.
      $linkText.val(selectedText);
    }

    const kbox = new KBox($html, {
      title: this.name,
      destroy: true,
      modal: true,
      id: 'link-modal',
      container: $('body'),
      position: 'none',
    });
    kbox.open();

    updateRequiredTarget();
    updateSubmitButton();

    // Focus the link text field to remove focus from the editor tools button.
    $linkText.trigger('focus');

    ev.preventDefault();
    return false;
  }
}

/**
 * The media helper.
 */
class MediaButton extends InsertButton {
  constructor() {
    super(gettext('Insert media...'), '', 'btn-media');
  }

  openModal(ev) {
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
            '<button type="submit" class="submit-button search-button" title="' + gettext('Search Gallery') + '">' +
            gettext('Search Gallery') + '</button>' +
          '</form>' +
          '<div class="locale-filter">' + gettext('Show media for:') + ' <select></select>' +
          '</div>' +
        '</div>' +
        '<div class="placeholder">' + '</div>' +
          '<div class="submit sumo-button-wrap reverse-on-desktop align-end">' +
            '<button class="sumo-button primary-button">' + gettext('Insert Media') + '</button>' +
            '<a href="' + galleryUrl + '#upload" class="upload sumo-button secondary-button" target="_blank">' +
            gettext('Upload Media') + '</a>' +
            '<a href="#cancel" class="kbox-cancel sumo-button push-left">' + gettext('Cancel') + '</a>' +
          '</div>' +
      '</section>'
  ),
      selectedText = me.getSelectedText(),
      mediaQ = '',
      mediaLocale = $('html').attr('lang'),
      mediaPage = 1,
      kbox;

    // Handle locale filter
    var $lf = $html.find('div.locale-filter select');
    $lf.html($('#_languages-select-box').html());
    $lf.on('change', function() {
      mediaPage = 1;
      mediaLocale = $(this).val();
      updateResults();
    });

    // Handle Search
    $html.find('form#gallery-modal-search').on('submit', function(e) {
      mediaQ = $html.find('input[name="q"]').val();
      mediaPage = 1;
      updateResults();
      e.preventDefault();
      return false;
    });

    // Handle Upload link
    $html.find('a.upload').on("click", function(e) {
      // Close the modal. The link itself will open gallery in new tab/window.
      kbox.close();
    });

    // Handle pagination
    $html.on('click', 'ol.pagination a', function(e) {
      mediaPage = parseInt($(this).attr('href').split('&page=')[1], 10);
      updateResults();
      e.preventDefault();
      return false;
    });

    // Handle 'Insert Media' button click
    $html.find('div.submit button').on("click", function(e) {
      // Generate the wiki markup based on what the user has selected.
      me.reset();

      var $selected = $html.find('#media-list > li.selected');
      if ($selected.length < 1) {
        alert(gettext('Please select an image to insert.'));
        return false;
      }

      me.markup = '[[Image:' + $selected.find('a').attr('title') + ']]';

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
        data: {q: mediaQ, page: mediaPage,
          locale: mediaLocale},
        dataType: 'html',
        success: function(html) {
          $html.find('div.placeholder').html(html);
          $html.find('#media-list > li').on("click", function(e) {
            let $this = $(this);
            let $mediaList = $(this).parent();
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
}

/**
 * The canned responses helper
 */
class CannedResponsesButton extends InsertButton {
  permissionBits = [];

  constructor() {
    super(gettext('Common responses'), '', 'btn-cannedresponses');

    this.html = '<a class="markup-toolbar-link" href="#"/>';
  }

  /**
   * Gets the DOM node for the button.
   */
  node() {
    const me = this,
      $btn = this.render();
    $btn.on('click', function(e) {
      me.openModal(e);
    });

    me.getPermissionBits();

    return $btn[0];
  }

  getPermissionBits() {
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

  openModal(e) {
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
          '<ul class="category-list">' +
          '<li class="status-indicator busy">' + gettext('Loading...') + '</li>' +
          '</ul></div>' +
          '<div id="response-list-area">' +
          '<h2 class="heading-label">' + gettext('Responses') + '</h2>' +
          '<h4 class="nocat-label">' + gettext('Please select a category from the previous column or start a search.') + '</h4>' +
          '<p class="response-list"/>' +
          '</div>' +
          '<div id="response-content-area">' +
          '<h2 class="heading-label preview-label">' + gettext('Response editor') + '</h2>' +
          '<div class="sumo-button-wrap">' +
          '<button class="toggle-view sumo-button">' + gettext('Switch to preview mode') + '</button>' +
          '</div>' +
          '<div class="field has-md-textarea response-preview is-condensed">' +
          '<textarea id="response-content">' +
          '</textarea></div>' +
          '<p class="response-preview-rendered"></p>' +
          '</div>' +
          '</div>' +
          '</div>' +
          '<div class="placeholder" /><div class="submit sumo-button-wrap" id="response-submit-area">' +
          '<button id="insert-response" class="sumo-button primary-button">' + gettext('Insert Response') + '</button>' +
          '<a href="#cancel" class="sumo-button secondary-button kbox-cancel">' + gettext('Cancel') + '</a>' +
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
      var slug = $('#response-content').data('slug');
      trackEvent('common_forum_response_insert', {slug});

      me.markup = $('#response-content').val();
      me.handleClick(e);
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
                $response.on("click", function() {
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

    $html.find('#insert-response').on("click", function() {
      insertResponse();
      kbox.close();
    });

    $html.find('#filter-responses-field').on('keyup', function() {
      var term = $(this).val();
      searchResponses(term);
    });

    var $previewLabel = $html.find('.preview-label');
    var $contentArea = $html.find('.response-preview');
    var $renderedPreview = $html.find('.response-preview-rendered');

    $html.find('.toggle-view').on("click", function() {
      if ($contentArea.is(':visible')) {
        updatePreview();
        $previewLabel.text(gettext('Response preview'));
        $(this).text(gettext('Switch to edit mode'));

        $contentArea.hide();
        $renderedPreview.show();
      } else {
        $previewLabel.text(gettext('Response editor'));
        $(this).text(gettext('Switch to preview mode'));

        $contentArea.show();
        $renderedPreview.hide();
      }
    });

    e.preventDefault();
    return false;
  }
}

/**
 * The quote button helper (for private messages)
 */
class QuoteButton extends InsertButton {
  constructor() {
    var previousContent = $('#read-message').attr('data-message-content');
    var previousAuthor = $('.from a').text();
    var previousAuthorLink = $('.from a').attr('href');
    var quote = '[' + previousAuthorLink + ' ' + previousAuthor + '] ' +
      gettext('said') + '\r\n';
    quote += '<blockquote>\r\n';
    quote += previousContent + '\r\n';
    quote += '</blockquote>\r\n';

    super(gettext('Quote previous message...'), quote, 'btn-quote');
  }
}

Marky.SimpleButton = SimpleButton;
Marky.MarkupButton = MarkupButton;
Marky.InsertButton = InsertButton;
Marky.Separator = Separator;
Marky.LinkButton = LinkButton;
Marky.MediaButton = MediaButton;
Marky.CannedResponsesButton = CannedResponsesButton;
Marky.QuoteButton = QuoteButton;

export default Marky;
