import trackEvent from "sumo/js/analytics";
import KBox from "sumo/js/kbox";
import { apiFetch } from "sumo/js/utils/fetch";

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

// Parse an HTML string into its first element.
function parseHTML(html) {
  var template = document.createElement("template");
  template.innerHTML = html.trim();
  return template.content.firstElementChild;
}

// Parse an HTML string (e.g. an ajax response) into a document we can query.
function parseDoc(html) {
  return new DOMParser().parseFromString(html, "text/html");
}

// Show/hide mirroring jQuery's .show()/.hide(): reveal elements hidden by an
// inline style, a CSS rule, or the `hidden` attribute (restoring a sensible
// default display for the tag).
function show(el) {
  if (!el) {
    return;
  }
  el.hidden = false;
  el.style.display = "";
  if (window.getComputedStyle(el).display === "none") {
    el.style.display = el.tagName === "LI" ? "list-item" : "block";
  }
}

function hide(el) {
  if (el) {
    el.style.display = "none";
  }
}

function isVisible(el) {
  return !!(el && el.offsetParent !== null);
}

// A small type-ahead for a text <input>: fetch suggestions via `source(term,
// cb)`, show them in a dropdown with keyboard/mouse selection, and call
// `onSelect(item)` when one is chosen. Replaces the old jQuery-UI autocomplete.
function attachTypeahead(input, source, onSelect) {
  if (!input) {
    return;
  }
  var list = document.createElement("ul");
  list.className = "marky-autocomplete";
  list.hidden = true;
  input.insertAdjacentElement("afterend", list);

  var items = [];
  var activeIndex = -1;
  var debounceTimer;

  function close() {
    list.hidden = true;
    list.innerHTML = "";
    items = [];
    activeIndex = -1;
  }

  function highlight(idx) {
    activeIndex = idx;
    Array.prototype.forEach.call(list.children, function (li, i) {
      li.classList.toggle("active", i === idx);
    });
  }

  function pick(idx) {
    var item = items[idx];
    if (!item) {
      return;
    }
    onSelect(item);
    close();
  }

  function render(results) {
    items = results || [];
    list.innerHTML = "";
    if (!items.length) {
      close();
      return;
    }
    items.forEach(function (item, i) {
      var li = document.createElement("li");
      li.textContent = item.label;
      // mousedown (not click) so it fires before the input's blur closes the list.
      li.addEventListener("mousedown", function (e) {
        e.preventDefault();
        pick(i);
      });
      list.appendChild(li);
    });
    activeIndex = -1;
    list.hidden = false;
  }

  input.addEventListener("input", function () {
    clearTimeout(debounceTimer);
    var term = input.value;
    if (!term) {
      close();
      return;
    }
    debounceTimer = setTimeout(function () {
      source(term, render);
    }, 300);
  });

  input.addEventListener("keydown", function (e) {
    if (list.hidden) {
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      highlight(Math.min(activeIndex + 1, items.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      highlight(Math.max(activeIndex - 1, 0));
    } else if (e.key === "Enter") {
      if (activeIndex >= 0) {
        e.preventDefault();
        pick(activeIndex);
      }
    } else if (e.key === "Escape") {
      close();
    }
  });

  // Delay so an item's mousedown registers before we hide the list.
  input.addEventListener("blur", function () {
    setTimeout(close, 150);
  });
}

var Marky = {
  createSimpleToolbar: function (toolbarSel, textareaSel, options) {
    var defaults = {
      cannedResponses: false,
      privateMessaging: false,
    };

    var settings = Object.assign({}, defaults, options);

    var SB = Marky.SimpleButton;
    var buttons = [
      new SB(gettext("Bold"), "'''", "'''", gettext("bold text"), "btn-bold"),
      new SB(gettext("Italic"), "''", "''", gettext("italic text"), "btn-italic"),
      new Marky.Separator(),
      new Marky.LinkButton(),
      new Marky.Separator(),
      new SB(gettext("Numbered List"), "# ", "", gettext("Numbered list item"), "btn-ol", true),
      new SB(gettext("Bulleted List"), "* ", "", gettext("Bulleted list item"), "btn-ul", true),
    ];
    if (settings.mediaButton) {
      buttons.splice(4, 0, new Marky.MediaButton());
    }
    if (settings.cannedResponses) {
      buttons.push(new Marky.Separator(), new Marky.CannedResponsesButton());
    }
    if (settings.privateMessaging) {
      buttons.push(new Marky.Separator(), new Marky.QuoteButton());
    }

    Marky.createCustomToolbar(toolbarSel, textareaSel, buttons);
  },
  createFullToolbar: function (toolbarSel, textareaSel) {
    Marky.createCustomToolbar(toolbarSel, textareaSel, Marky.allButtons());
  },
  createCustomToolbar: function (toolbarSel, textareaSel, partsArray) {
    var toolbar = document.querySelector(toolbarSel || ".editor-tools");
    var textarea = document.querySelector(textareaSel || "#reply-content, #id_content");
    if (!toolbar || !textarea) {
      return;
    }
    for (var i = 0, l = partsArray.length; i < l; i++) {
      toolbar.appendChild(partsArray[i].bind(textarea).node());
    }
  },
  allButtons: function () {
    var SB = Marky.SimpleButton;
    return [
      new SB(gettext("Bold"), "'''", "'''", gettext("bold text"), "btn-bold"),
      new SB(gettext("Italic"), "''", "''", gettext("italic text"), "btn-italic"),
      new Marky.Separator(),
      new Marky.LinkButton(),
      new Marky.MediaButton(),
      new Marky.Separator(),
      new SB(gettext("Numbered List"), "# ", "", gettext("Numbered list item"), "btn-ol", true),
      new SB(gettext("Bulleted List"), "* ", "", gettext("Bulleted list item"), "btn-ul", true),
      new Marky.Separator(),
      new SB(gettext("Heading 1"), "=", "=", gettext("Heading 1"), "btn-h1", true),
      new SB(gettext("Heading 2"), "==", "==", gettext("Heading 2"), "btn-h2", true),
      new SB(gettext("Heading 3"), "===", "===", gettext("Heading 3"), "btn-h3", true),
    ];
  },
};

/*
  * A simple button.
  * Note: `everyline` is a boolean value that says whether or not the selected
  *       text should be broken into multiple lines and have the markup applied
  *       to each line or not. Default is false (do not apply this behavior).
  *       `classes` is a list of classes to include in the output
  */
Marky.SimpleButton = function (name, openTag, closeTag, defaultText, classes, everyline) {
  this.name = name;
  this.classes = "";
  this.openTag = openTag;
  this.closeTag = closeTag;
  this.defaultText = defaultText;
  this.everyline = everyline;
  if (undefined !== classes) {
    this.classes = classes;
  }

  this.html = '<button class="markup-toolbar-button" type="button"></button>';
};

Marky.SimpleButton.prototype = {
  // Binds the button to a textarea (DOM node).
  bind: function (textarea) {
    this.textarea = textarea;
    return this;
  },
  // Renders the html.
  render: function () {
    var out = parseHTML(this.html);
    out.setAttribute("title", this.name);
    out.textContent = this.name;
    if (this.classes) {
      this.classes.split(/\s+/).forEach(function (cls) {
        if (cls) {
          out.classList.add(cls);
        }
      });
    }
    return out;
  },
  // Gets the DOM node for the button.
  node: function () {
    var me = this;
    var btn = this.render();
    btn.addEventListener("click", function (e) {
      me.handleClick(e);
    });
    return btn;
  },
  // Get selected text
  getSelectedText: function () {
    if (window.codemirror && window.highlighting && window.highlighting.isEnabled()) {
      return window.highlighting.editor.getSelection();
    }
    var textarea = this.textarea;
    return textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);
  },
  // Handles the button click.
  handleClick: function (e) {
    var selText, selStart, selEnd, splitText;
    var textarea = this.textarea;
    var scrollTop = textarea.scrollTop;
    var editor = window.highlighting && window.highlighting.editor;

    if (window.codemirror && window.highlighting && window.highlighting.isEnabled()) {
      selText = editor.somethingSelected() ? editor.getSelection() : this.defaultText;
      selText = this.openTag + selText + this.closeTag;
      editor.replaceSelection(selText);
      editor.focus();
      e.preventDefault();
      return false;
    }

    textarea.focus();

    selStart = textarea.selectionStart;
    selEnd = textarea.selectionEnd;
    selText = textarea.value.substring(selStart, selEnd);
    if (!selText.length) {
      selText = this.defaultText;
    }

    if (this.everyline && selText.indexOf("\n") !== -1) {
      splitText = this._applyEveryLine(this.openTag, this.closeTag, selText).join("\n");
      textarea.value =
        textarea.value.substring(0, selStart) +
        splitText +
        textarea.value.substring(selEnd);

      textarea.selectionStart = selStart;
      textarea.selectionEnd = selStart + splitText.length;
    } else {
      textarea.value =
        textarea.value.substring(0, selStart) +
        this.openTag + selText + this.closeTag +
        textarea.value.substring(selEnd);

      textarea.selectionStart = selStart + this.openTag.length;
      textarea.selectionEnd = textarea.selectionStart + selText.length;
    }

    textarea.scrollTop = scrollTop;
    e.preventDefault();
    return false;
  },
  _applyEveryLine: function (opentag, closetag, block) {
    return block.split("\n").map(function (line) {
      return line.replace(/\s+/, "").length ? opentag + line + closetag : line;
    });
  },
};

/*
  * A button separator.
  */
Marky.Separator = function () {
  this.html = '<span class="separator"></span>';
};

Marky.Separator.prototype = {
  node: function () {
    return parseHTML(this.html);
  },
  bind: function () {
    return this;
  },
};

/*
  * The link helper.
  */
Marky.LinkButton = function () {
  this.name = gettext("Insert a link...");
  this.classes = "btn-link";
  this.openTag = "[http://example.com ";
  this.closeTag = "]";
  this.defaultText = gettext("link text");
  this.everyline = false;

  this.origOpenTag = this.openTag;
  this.origCloseTag = this.closeTag;
  this.origDefaultText = this.defaultText;

  this.html = '<button class="markup-toolbar-button" type="button"></button>';
};

Marky.LinkButton.prototype = Object.assign({}, Marky.SimpleButton.prototype, {
  // Gets the DOM node for the button.
  node: function () {
    var me = this;
    var btn = this.render();
    btn.addEventListener("click", function (e) {
      me.openModal(e);
    });
    return btn;
  },
  reset: function () {
    this.openTag = this.origOpenTag;
    this.closeTag = this.origCloseTag;
    this.defaultText = this.origDefaultText;
  },
  openModal: function (ev) {
    var me = this;
    var html = parseHTML(
      '<section class="marky">' +
        '<div class="field">' +
        "<label>" + gettext("Link text:") + "</label>" +
        '<input type="text" name="link-text" />' +
        "</div>" +
        '<div class="field">' +
        "<label>" + gettext("Link target:") + "</label>" +
        '<ol><li class="field"><div class="field radio is-condensed"><input type="radio" name="link-type" id="id_link-type-internal" value="internal" /><label for="id_link-type-internal">' +
        gettext("Support article:") + "</label></div>" +
        '<input type="text" name="internal" placeholder="' +
        gettext("Enter the name of the article") + '" /></li>' +
        '<li class="field"><div class="field radio is-condensed"><input type="radio" name="link-type" id="id_link-type-external" value="external" /><label for="id_link-type-external">' +
        gettext("External link:") + "</label></div>" +
        '<input type="text" name="external" placeholder="' +
        gettext("Enter the URL of the external link") + '" /></li>' +
        '</ol><div class="submit sumo-button-wrap align-full reverse-on-desktop"><button type="button" class="sumo-button primary-button"></button>' +
        '<a href="#cancel" class="kbox-cancel sumo-button secondary-button">' + gettext("Cancel") +
        "</a></div></section>"
    );
    var selectedText = me.getSelectedText();
    var kbox;

    html.querySelectorAll('li input[type="text"]').forEach(function (input) {
      input.addEventListener("focus", function () {
        var radio = input.closest("li").querySelector('input[type="radio"]');
        if (radio) {
          radio.click();
        }
      });
    });

    // Perform a query for the sections of an article if last character is a pound:
    var performSectionSearch = function (term) {
      return term.indexOf("#") === term.length - 1;
    };

    var results = [];

    // Get the article URL by providing the article name:
    var getArticleURL = function (name) {
      for (var i = 0; i < results.length; i++) {
        if (name === results[i].label) {
          return results[i].url;
        }
      }
      return null;
    };

    var articleSearch = function (term, response) {
      results = [];
      apiFetch("/en-US/search", {
        method: "GET",
        data: {
          format: "json",
          q: term,
          a: 1,
          w: 1,
          language: document.documentElement.lang,
        },
        dataType: "json",
      }).then(function (data) {
        (data.results || []).forEach(function (val) {
          results.push({ label: val.title, url: val.url });
        });
        response(results);
      });
    };

    var sectionSearch = function (term, response) {
      var articleName = term.split("#")[0];
      var articleURL = getArticleURL(articleName);

      if (!articleURL) {
        return;
      }

      apiFetch(articleURL, { method: "GET", dataType: "text" }).then(function (data) {
        var headings = parseDoc(data).querySelectorAll("[id^='w_']");
        var array = [];

        if (headings.length === 0) {
          array.push({
            label: gettext("No sections found"),
            value: term.replace("#", ""),
            target: "",
          });
        }

        headings.forEach(function (heading) {
          var label = heading.textContent;
          var target = heading.getAttribute("id");
          var value = term + target;
          array.push({ label: label, value: value, target: target });
        });
        response(array);
      });
    };

    var internalInput = html.querySelector('input[name="internal"]');
    attachTypeahead(
      internalInput,
      function (term, response) {
        if (performSectionSearch(term)) {
          sectionSearch(term, response);
        } else {
          articleSearch(term, response);
        }
      },
      function (item) {
        internalInput.value = item.value !== undefined ? item.value : item.label;
        if (item.target) {
          var linktext = html.querySelector("input[name=link-text]");
          if (linktext && linktext.value === "") {
            linktext.value = item.label;
          }
        }
      }
    );

    var insertButton = html.querySelector("button");
    insertButton.textContent = gettext("Insert Link");
    insertButton.addEventListener("click", function (e) {
      // Generate the wiki markup based on what the user has selected
      // (internal vs external links) and entered into the textboxes,
      // if anything.
      var checked = html.querySelector('input[type="radio"]:checked');
      var val = checked ? checked.value : undefined;
      var text = html.querySelector("input[name=link-text]").value;
      var internal = html.querySelector('input[name="internal"]');
      var external = html.querySelector('input[name="external"]');
      me.reset();
      if (val === "internal") {
        var title = internal.value;
        if (title) {
          if (title === selectedText) {
            // The title wasn't changed, so lets keep it selected.
            me.openTag = "[[";
            me.closeTag = "]]";
            if (text) {
              me.closeTag = "|" + text + me.closeTag;
            }
          } else {
            // The title changed, so lets insert link before the cursor.
            me.openTag = "[[" + title;
            if (text) {
              me.openTag += "|" + text;
            }
            me.openTag += "]] ";
            me.closeTag = "";
            me.defaultText = "";
          }
        } else {
          me.openTag = "[[";
          me.closeTag = "]]";
          if (text) {
            me.closeTag = "|" + text + "]]";
          }
          me.defaultText = gettext("Knowledge Base Article");
        }
      } else {
        var link = external.value;
        if (link) {
          if (link.indexOf("http") !== 0) {
            link = "http://" + link;
          }
          me.openTag = "[" + link + " ";
          if (text) {
            me.openTag += text + "] ";
            me.closeTag = "";
            me.defaultText = "";
          }
        } else if (text) {
          me.defaultText = text;
        }
      }

      me.handleClick(e);
      kbox.close();
    });

    if (selectedText) {
      // If the user has selected text, lets default to it being the Article Title.
      internalInput.value = selectedText;
      internalInput.focus();
    }

    kbox = new KBox(html, {
      title: this.name,
      destroy: true,
      modal: true,
      id: "link-modal",
      container: document.body,
      position: "none",
    });
    kbox.open();

    ev.preventDefault();
    return false;
  },
});

/*
  * The media helper.
  */
Marky.MediaButton = function () {
  this.name = gettext("Insert media...");
  this.classes = "btn-media";
  this.openTag = "";
  this.closeTag = "";
  this.defaultText = gettext("media");
  this.everyline = false;

  this.html = '<button class="markup-toolbar-button" type="button"></button>';
};

Marky.MediaButton.prototype = Object.assign({}, Marky.SimpleButton.prototype, {
  // Gets the DOM node for the button.
  node: function () {
    var me = this;
    var btn = this.render();
    btn.addEventListener("click", function (e) {
      me.openModal(e);
    });
    return btn;
  },
  reset: function () {
    this.openTag = "";
    this.closeTag = "";
    this.defaultText = "";
  },
  openModal: function (ev) {
    var me = this;
    var editorEl = me.textarea.closest(".editor");
    var mediaSearchUrl = editorEl ? editorEl.dataset.mediaSearchUrl : undefined;
    var galleryUrl = editorEl ? editorEl.dataset.mediaGalleryUrl : "";
    var html = parseHTML(
      '<section class="marky">' +
        '<div class="filter cf">' +
        '<form class="simple-search-form" id="gallery-modal-search"><input type="text" name="q" class="searchbox"' +
        'placeholder="' + gettext("Search Gallery") + '" />' +
        '<button type="submit" class="submit-button search-button" title="' + gettext("Search Gallery") + '">' +
        gettext("Search Gallery") + "</button>" +
        "</form>" +
        '<div class="locale-filter">' + gettext("Show media for:") + " <select></select>" +
        "</div>" +
        "</div>" +
        '<div class="placeholder"></div>' +
        '<div class="submit sumo-button-wrap reverse-on-desktop align-end">' +
        '<button class="sumo-button primary-button">' + gettext("Insert Media") + "</button>" +
        '<a href="' + galleryUrl + '#upload" class="upload sumo-button secondary-button" target="_blank">' +
        gettext("Upload Media") + "</a>" +
        '<a href="#cancel" class="kbox-cancel sumo-button push-left">' + gettext("Cancel") + "</a>" +
        "</div>" +
        "</section>"
    );
    var mediaQ = "";
    var mediaLocale = document.documentElement.lang;
    var mediaPage = 1;
    var kbox;

    // Handle locale filter
    var localeSelect = html.querySelector("div.locale-filter select");
    var languagesBox = document.getElementById("_languages-select-box");
    if (languagesBox) {
      localeSelect.innerHTML = languagesBox.innerHTML;
    }
    localeSelect.addEventListener("change", function () {
      mediaPage = 1;
      mediaLocale = localeSelect.value;
      updateResults();
    });

    // Handle Search
    html.querySelector("form#gallery-modal-search").addEventListener("submit", function (e) {
      mediaQ = html.querySelector('input[name="q"]').value;
      mediaPage = 1;
      updateResults();
      e.preventDefault();
    });

    // Handle Upload link
    var uploadLink = html.querySelector("a.upload");
    uploadLink.addEventListener("click", function (e) {
      // Open the gallery ourselves, then close. Closing destroys the modal DOM
      // (destroy: true), which detaches this link before the browser can follow
      // it - so relying on the anchor's own navigation would open nothing.
      e.preventDefault();
      window.open(uploadLink.href, "_blank", "noopener");
      kbox.close();
    });

    // Handle pagination
    html.addEventListener("click", function (e) {
      var link = e.target.closest("ol.pagination a");
      if (!link || !html.contains(link)) {
        return;
      }
      mediaPage = parseInt(link.getAttribute("href").split("&page=")[1], 10);
      updateResults();
      e.preventDefault();
    });

    // Handle 'Insert Media' button click
    html.querySelector("div.submit button").addEventListener("click", function (e) {
      // Generate the wiki markup based on what the user has selected.
      me.reset();

      var selected = html.querySelector("#media-list > li.selected");
      if (!selected) {
        alert(gettext("Please select an image to insert."));
        return;
      }

      me.openTag = "[[Image";
      me.openTag += ":" + selected.querySelector("a").getAttribute("title") + "]] ";

      me.handleClick(e);
      kbox.close();
    });

    updateResults();

    // Update the media list via ajax call.
    function updateResults() {
      html.classList.add("processing");
      apiFetch(mediaSearchUrl, {
        method: "GET",
        data: { q: mediaQ, page: mediaPage, locale: mediaLocale },
        dataType: "html",
      })
        .then(function (resultHtml) {
          html.querySelector("div.placeholder").innerHTML = resultHtml;
          html.querySelectorAll("#media-list > li").forEach(function (li) {
            li.addEventListener("click", function (e) {
              var mediaList = li.parentNode;
              var current = mediaList.querySelector("li.selected");
              if (current) {
                current.classList.remove("selected");
              }
              li.classList.add("selected");
              e.preventDefault();
            });
          });
        })
        .catch(function () {
          var message = gettext("Oops, there was an error.");
          html.querySelector("div.placeholder").innerHTML =
            '<div class="msg">' + message + "</div>";
        })
        .finally(function () {
          html.classList.remove("processing");
        });
    }

    kbox = new KBox(html, {
      title: this.name,
      destroy: true,
      modal: true,
      id: "media-modal",
      container: document.body,
      position: "none",
    });
    kbox.open();

    ev.preventDefault();
    return false;
  },
});

/*
  * The canned responses helper
  */
Marky.CannedResponsesButton = function () {
  this.name = gettext("Common responses");
  this.classes = "btn-cannedresponses";
  this.openTag = "";
  this.closeTag = "";
  this.defaultText = "cannedresponses";
  this.everyline = false;

  this.html = '<a class="markup-toolbar-link" href="#"></a>';
};

Marky.CannedResponsesButton.prototype = Object.assign({}, Marky.SimpleButton.prototype, {
  // Gets the DOM node for the button.
  node: function () {
    var me = this;
    var btn = this.render();
    btn.addEventListener("click", function (e) {
      me.openModal(e);
    });

    me.getPermissionBits();

    return btn;
  },
  reset: function () {
    this.openTag = "";
    this.closeTag = "";
    this.defaultText = "";
  },
  openModal: function (e) {
    var me = this;
    var html = parseHTML(
      '<section class="marky">' +
        '<div class="search simple-search-form">' +
        '<input type="text" name="q" id="filter-responses-field" placeholder="' +
        gettext("Search for common responses") + '" class="searchbox"/>' +
        "</div></div>" +
        '<div class="area">' +
        '<div id="responses-area">' +
        '<h2 class="heading-label">' + gettext("Categories") + "</h2>" +
        '<ul class="category-list">' +
        '<li class="status-indicator busy">' + gettext("Loading...") + "</li>" +
        "</ul></div>" +
        '<div id="response-list-area">' +
        '<h2 class="heading-label">' + gettext("Responses") + "</h2>" +
        '<h4 class="nocat-label">' + gettext("Please select a category from the previous column or start a search.") + "</h4>" +
        '<p class="response-list"></p>' +
        "</div>" +
        '<div id="response-content-area">' +
        '<h2 class="heading-label preview-label">' + gettext("Response editor") + "</h2>" +
        '<div class="sumo-button-wrap">' +
        '<button class="toggle-view sumo-button">' + gettext("Switch to preview mode") + "</button>" +
        "</div>" +
        '<div class="field has-md-textarea response-preview is-condensed">' +
        '<textarea id="response-content">' +
        "</textarea></div>" +
        '<p class="response-preview-rendered"></p>' +
        "</div>" +
        "</div>" +
        "</div>" +
        '<div class="placeholder"></div><div class="submit sumo-button-wrap" id="response-submit-area">' +
        '<button id="insert-response" class="sumo-button primary-button">' + gettext("Insert Response") + "</button>" +
        '<a href="#cancel" class="sumo-button secondary-button kbox-cancel">' + gettext("Cancel") + "</a>" +
        "</div>" +
        "</section>"
    );
    var kbox;

    var cannedResponsesUrl = "/kb/common-forum-responses";
    var previewUrl = "answer-preview-async";

    function updatePreview() {
      var response = html.querySelector("#response-content").value;
      var tokenEl = document.querySelector("[name=csrfmiddlewaretoken]");
      var token = tokenEl ? tokenEl.getAttribute("value") : "";

      toggleThrobber(true);

      apiFetch(previewUrl, {
        method: "POST",
        data: { content: response, csrfmiddlewaretoken: token },
        dataType: "html",
      })
        .then(function (previewHtml) {
          var container = html.querySelector(".response-preview-rendered");
          var rendered = parseDoc(previewHtml).querySelector(".main-content");
          container.innerHTML = "";
          if (rendered) {
            container.appendChild(rendered);
          }
        })
        .finally(function () {
          toggleThrobber(false);
        });
    }

    function getContent(articleUrl) {
      // If the article doesn't exist, it has /new in its URL.
      // Don't query nonexisting articles.
      if (!articleUrl || articleUrl.indexOf("/new") !== -1) {
        return;
      }

      toggleThrobber(true);

      apiFetch(articleUrl + "/edit", { method: "GET", dataType: "html" })
        .then(function (data) {
          var content = parseDoc(data).querySelector("#id_content");
          var textbox = html.querySelector("#response-content");
          textbox.value = content ? content.value : "";
          textbox.dataset.slug = articleUrl;
          updatePreview();
        })
        .finally(function () {
          toggleThrobber(false);
        });
    }

    function toggleThrobber(busy) {
      var label = html.querySelector(".preview-label");
      if (!label) {
        return;
      }
      label.classList.toggle("busy", !!busy);
    }

    function isAllowedToUseResponse(responseTarget) {
      if (responseTarget.indexOf("#") === -1) {
        // No permission markers: Everyone's allowed
        return true;
      }

      var permBits = responseTarget.split("#")[1];

      for (var i = 0; i < permBits.length; i++) {
        if (me.permissionBits.indexOf(permBits[i]) !== -1) {
          return true;
        }
      }
      return false;
    }

    function insertResponse() {
      var content = html.querySelector("#response-content");
      var sourceContent = content.value;
      var slug = content.dataset.slug;
      var responseTextbox = document.getElementById("id_content");
      if (!responseTextbox) {
        return;
      }

      trackEvent("common_forum_response_insert", { slug: slug });

      responseTextbox.value = responseTextbox.value + sourceContent;
    }

    function searchResponses(term) {
      term = term.toLowerCase().trim();
      var searchHeading = html.querySelector("#response-list-area .heading-label");
      var noCategorySelected = html.querySelector(".nocat-label");
      var responseLists = html.querySelectorAll(".response-list ul");
      var responses = html.querySelectorAll(".response");
      var responseListArea = html.querySelector("#response-list-area");
      var responsesArea = html.querySelector("#responses-area");

      if (term === "") {
        searchHeading.textContent = gettext("Responses");
        responseListArea.classList.remove("filtered");
        responsesArea.classList.remove("filtered");
        show(noCategorySelected);
        responses.forEach(show);
        responseLists.forEach(hide);
        return;
      }

      responseListArea.classList.add("filtered");
      responsesArea.classList.add("filtered");
      searchHeading.textContent = gettext("Matching responses");
      hide(noCategorySelected);
      responseLists.forEach(show);

      responses.forEach(function (response) {
        if (response.textContent.toLowerCase().indexOf(term) === -1) {
          hide(response);
        } else {
          show(response);
        }
      });
    }

    function loadCannedResponses() {
      var siteLanguage = window.location.pathname.split("/")[1];
      var targetUrl = "/" + siteLanguage + cannedResponsesUrl;

      apiFetch(targetUrl, { method: "GET", dataType: "html" })
        .then(function (responseHtml) {
          var categoryList = html.querySelector(".category-list");
          var responsesList = html.querySelector(".response-list");
          var categories = parseDoc(responseHtml).querySelectorAll("[id^=w_]");
          var noCatLabel = html.querySelector(".nocat-label");

          categoryList.innerHTML = "";
          responsesList.innerHTML = "";

          categories.forEach(function (category) {
            var label = category.textContent;
            var headingItem = document.createElement("li");
            var responsesUl = document.createElement("ul");
            responsesUl.classList.add("sidebar-nav");
            hide(responsesUl);

            // Anchors between this heading and the next w_ heading.
            var sibling = category.nextElementSibling;
            while (sibling && !(sibling.id && sibling.id.indexOf("w_") === 0)) {
              sibling.querySelectorAll("a").forEach(function (anchor) {
                var responseItem = document.createElement("li");
                responseItem.classList.add("response");
                responseItem.textContent = anchor.textContent;
                var responseTarget = anchor.getAttribute("href");
                var canUseResponse = isAllowedToUseResponse(responseTarget);
                var targetUrlNoPerm = responseTarget.split("#")[0];

                if (canUseResponse) {
                  responseItem.addEventListener("click", function () {
                    html.querySelectorAll(".response-list li").forEach(function (li) {
                      if (li !== responseItem) {
                        li.classList.remove("selected");
                      }
                    });
                    responseItem.classList.add("selected");
                    getContent(targetUrlNoPerm);
                  });

                  responsesUl.appendChild(responseItem);
                }
              });
              sibling = sibling.nextElementSibling;
            }

            headingItem.classList.add("response-heading");
            headingItem.textContent = label;
            headingItem.addEventListener("click", function () {
              hide(noCatLabel);
              responsesList.querySelectorAll("ul").forEach(function (ul) {
                if (ul !== responsesUl) {
                  hide(ul);
                }
              });
              categoryList.querySelectorAll(".response-heading").forEach(function (heading) {
                if (heading !== headingItem) {
                  heading.classList.remove("selected");
                }
              });
              headingItem.classList.add("selected");
              show(responsesUl);
            });

            categoryList.appendChild(headingItem);
            responsesList.appendChild(responsesUl);
          });
        })
        .catch(function () {
          var statusIndicator = html.querySelector(".status-indicator");
          if (statusIndicator) {
            statusIndicator.classList.remove("busy");
            statusIndicator.textContent = gettext("There was an error checking for canned responses.");
          }
        });

      // return true so that the kbox actually opens:
      return true;
    }

    kbox = new KBox(html, {
      title: this.name,
      destroy: true,
      modal: true,
      id: "media-modal",
      container: document.body,
      position: "none",
      preOpen: loadCannedResponses,
    });

    kbox.open();

    html.querySelector("#insert-response").addEventListener("click", function () {
      insertResponse();
      kbox.close();
    });

    html.querySelector("#filter-responses-field").addEventListener("keyup", function (ev) {
      searchResponses(ev.target.value);
    });

    var previewLabel = html.querySelector(".preview-label");
    var contentArea = html.querySelector(".response-preview");
    var renderedPreview = html.querySelector(".response-preview-rendered");

    html.querySelector(".toggle-view").addEventListener("click", function (ev) {
      var toggle = ev.currentTarget;
      if (isVisible(contentArea)) {
        updatePreview();
        previewLabel.textContent = gettext("Response preview");
        toggle.textContent = gettext("Switch to edit mode");

        hide(contentArea);
        show(renderedPreview);
      } else {
        previewLabel.textContent = gettext("Response editor");
        toggle.textContent = gettext("Switch to preview mode");

        show(contentArea);
        hide(renderedPreview);
      }
    });

    e.preventDefault();
    return false;
  },

  permissionBits: [],

  getPermissionBits: function () {
    var me = this;
    var userLink = document.querySelector("#aux-nav .user");
    var profileLink = userLink ? userLink.getAttribute("href") : "";
    if (!profileLink) {
      return;
    }

    apiFetch(profileLink, { method: "GET", dataType: "html" }).then(function (data) {
      var userGroups = parseDoc(data).querySelectorAll("#groups li");
      userGroups.forEach(function (li) {
        var group = li.textContent;

        // Contributors:
        if (group === "Contributors") {
          me.permissionBits.push("c");
        }

        // Moderators:
        if (group === "Forum Moderators") {
          me.permissionBits.push("m");
        }

        // Administrators:
        if (group === "Administrators") {
          me.permissionBits.push("a");
        }
      });
    });
  },
});

/*
  * The quote button helper
  */
Marky.QuoteButton = function () {
  var name = gettext("Quote previous message...");
  var readMessage = document.getElementById("read-message");
  var previousContent = readMessage ? readMessage.getAttribute("data-message-content") : "";
  var fromLink = document.querySelector(".from a");
  var previousAuthor = fromLink ? fromLink.textContent : "";
  var previousAuthorLink = fromLink ? fromLink.getAttribute("href") : "";
  var quote = "[" + previousAuthorLink + " " + previousAuthor + "] " +
    gettext("said") + "\r\n";
  quote += "<blockquote>\r\n";
  quote += previousContent + "\r\n";
  quote += "</blockquote>\r\n";

  return new Marky.SimpleButton(name, quote, "", "", "btn-quote", true);
};

export { attachTypeahead, parseDoc };
export default Marky;
