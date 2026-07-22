import spinnerImg from "sumo/img/spinner.gif";
import { lazyload, loadAllImages } from "sumo/js/utils/lazyload";
import { apiFetch } from "sumo/js/utils/fetch";
import { setCookie, removeCookie } from "sumo/js/utils/cookie";
import { slideUp, slideDown, slideToggle, serialize } from "sumo/js/utils/dom";
import { URLify } from "sumo/js/libs/django/urlify";
import KBox from "sumo/js/kbox";
import CodeMirror from "codemirror";
import "codemirror/addon/mode/simple";
import "codemirror/addon/hint/show-hint";
import "sumo/js/codemirror.sumo-hint";
import "sumo/js/codemirror.sumo-mode";
import "sumo/js/protocol";
import Modal from "protocol/js/modal";
import AjaxPreview from "sumo/js/ajaxpreview";
import { initDiff } from "sumo/js/diff";
import Marky from "sumo/js/markup";
import ShowFor from "sumo/js/showfor";
import collapsibleAccordionInit from "sumo/js/protocol-details-init";

/*
 * wiki.js
 * Scripts for the wiki app.
 */

// Show/hide matching jQuery's .show()/.hide(). Several elements here are hidden
// by the `hidden` attribute (#draft-message) or a CSS rule (#preview-bottom:
// `display: none`), not inline display - so clearing inline display alone won't
// reveal them (jQuery's .show() forced an explicit display). Clear the hidden
// attribute + inline display, and if a stylesheet still hides it, force block.
function show(el) {
  if (!el) {
    return;
  }
  el.hidden = false;
  el.style.display = "";
  if (window.getComputedStyle(el).display === "none") {
    el.style.display = "block";
  }
}

function hide(el) {
  if (el) {
    el.style.display = "none";
  }
}

function init() {
  var body = document.body;

  document.querySelectorAll('select.enable-if-js').forEach(function (el) {
    el.disabled = false;
  });

  if (body.classList.contains('new')) {
    initPrepopulatedSlugs();
  }

  initDetailsTags();

  if (body.classList.contains('review')) { // Review pages
    new ShowFor();
    initNeedsChange();

    loadAllImages();

    // We can enable the buttons now.
    document.querySelectorAll('#actions input').forEach(function (el) {
      el.disabled = false;
    });
  }

  if (body.matches('.edit_metadata, .edit, .new, .translate')) { // Document form page
    // Submit form
    var comment = document.getElementById('id_comment');
    if (comment) {
      comment.addEventListener('keypress', function (e) {
        if (e.which === 13) {
          comment.blur();
          var form = comment.closest('form');
          var submit = form && form.querySelector('[type=submit]');
          if (submit) {
            submit.click();
          }
          e.preventDefault();
        }
      });
    }

    initExitSupportFor();
    initArticlePreview();
    initPreviewDiff();
    initTitleAndSlugCheck();
    initNeedsChange();
    initFormLock();

    loadAllImages();

    // We can enable the buttons now.
    document.querySelectorAll('.submit input').forEach(function (el) {
      el.disabled = false;
    });
  }

  if (body.matches('.edit, .new, .translate')) {
    initPreValidation();
    initSummaryCount();
    initCodeMirrorEditor();
  }

  if (body.classList.contains('translate')) {  // Translate page
    initToggleDiff();
    initTranslationDraft();
  }

  initEditingTools();

  initDiffPicker();

  Marky.createFullToolbar('.editor-tools', '#id_content');

  initReadyForL10n();

  initArticleApproveModal();

  initRevisionList();

  collapsibleContributorTools();

  lazyload();
}

function initArticleApproveModal() {
  if (!document.getElementById('approve-modal')) {
    return;
  }
  var onSignificanceClick = function (e) {
    // Hiding if the significance is typo.
    // .parentNode is because #id_is_ready_for_localization is inside a
    // <label>, as is the text
    var readyForL10n = document.getElementById('id_is_ready_for_localization');
    var parent = readyForL10n && readyForL10n.parentNode;
    if (!parent) {
      return;
    }
    if (e.target.id === 'id_significance_0') {
      parent.style.display = 'none';
    } else {
      parent.style.display = '';
    }
  };

  ['id_significance_0', 'id_significance_1', 'id_significance_2'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) {
      el.addEventListener('click', onSignificanceClick);
    }
  });
}

// Note <details> tag support (kept for the .no-details CSS hook). The old
// jQuery fallback for browsers without native <details> was removed: it was
// dead (all supported browsers implement <details>) and called $.browser,
// which jQuery removed in 1.9.
function initDetailsTags() {
  if (!('open' in document.createElement('details'))) {
    document.documentElement.className += ' no-details';
  }
}

// Auto-populate the slug field from the title (vanilla replacement for the old
// Django jquery.prepopulate plugin, which only this file used).
function initPrepopulatedSlugs() {
  var slug = document.getElementById('id_slug');
  var title = document.getElementById('id_title');
  if (!slug || !title) {
    return;
  }
  var maxLength = 50;
  slug.classList.add('prepopulated_field');

  // Stop auto-populating once the user edits the slug directly.
  var slugChanged = false;
  slug.addEventListener('change', function () {
    slugChanged = true;
  });

  title.addEventListener('change', function () {
    if (slugChanged) {
      return;
    }
    var raw = title.value;
    slug.value = URLify(raw, maxLength) || raw;
  });
}

function initSummaryCount() {
  var summaryCount = document.getElementById('remaining-characters');
  var summaryBox = document.getElementById('id_summary');
  if (!summaryCount || !summaryBox) {
    return;
  }
  // 160 characters is the maximum summary length of a Google result
  var warningCount = 160;
  var maxCount = parseInt(summaryCount.textContent, 10);

  function updateCount() {
    var currentCount = summaryBox.value.length;
    summaryCount.textContent = warningCount - currentCount;
    if (warningCount - currentCount >= 0) {
      summaryCount.style.color = 'black';
    } else {
      summaryCount.style.color = 'red';
      if (currentCount >= maxCount) {
        summaryBox.value = summaryBox.value.substr(0, maxCount);
      }
    }
  }

  updateCount();
  summaryBox.addEventListener('input', updateCount);
}

/*
 * Initialize the article preview functionality.
 */
export function initArticlePreview() {
  var previewEl = document.getElementById('preview');
  var previewBottom = document.getElementById('preview-bottom');
  var contentEl = document.getElementById('id_content');

  // AjaxPreview is a native EventTarget; listen with addEventListener and read
  // success off the CustomEvent detail (was a jQuery $(preview).on).
  function onDone(e) {
    if (e.detail.success) {
      show(previewBottom);
      new ShowFor();
      if (previewEl) {
        previewEl.querySelectorAll('select.enable-if-js').forEach(function (el) {
          el.disabled = false;
        });
        previewEl.querySelectorAll('.kbox').forEach(function (el) {
          new KBox(el);
        });
      }
      var output = document.querySelector('#preview-diff .output');
      if (output) {
        output.innerHTML = '';
      }
      collapsibleAccordionInit();
    }
  }

  // The submit button bar is rendered twice (top + the #preview-bottom bar
  // revealed after a preview), so wire a preview to each ".btn-preview"
  // (jQuery's AjaxPreview($('.btn-preview')) bound them all).
  document.querySelectorAll('.btn-preview').forEach(function (btn) {
    var preview = new AjaxPreview(btn, {
      contentElement: contentEl,
      previewElement: previewEl
    });
    preview.addEventListener('done', onDone);
  });
}

// Diff Preview of edits
export function initPreviewDiff() {
  var diff = document.getElementById('preview-diff');
  if (diff) {
    diff.classList.add('diff-this');
  }
  // The submit button bar is rendered twice (top + the #preview-bottom bar that
  // is revealed after a preview), so there are two ".btn-diff" buttons; wire
  // them all (jQuery's $('.btn-diff') bound the handler to every match).
  document.querySelectorAll('.btn-diff').forEach(function (diffButton) {
    diffButton.addEventListener('click', function () {
      var content = document.getElementById('id_content');
      var to = diff && diff.querySelector('.to');
      if (to && content) {
        to.textContent = content.value;
      }
      initDiff(diff ? diff.parentNode : undefined);
      show(document.getElementById('preview-bottom'));
      var preview = document.getElementById('preview');
      if (preview) {
        preview.innerHTML = '';
      }
    });
  });
}

export function initTitleAndSlugCheck() {
  var title = document.getElementById('id_title');
  var slug = document.getElementById('id_slug');

  if (title) {
    title.addEventListener('change', function () {
      var form = title.closest('form');
      verifyTitleUnique(title.value, form);
      // Check slug too, since it auto-updates and doesn't seem to fire
      // off change event.
      verifySlugUnique(slug ? slug.value : '', form);
    });
  }
  if (slug) {
    slug.addEventListener('change', function () {
      var form = slug.closest('form');
      verifySlugUnique(slug.value, form);
    });
  }

  function verifyTitleUnique(title, form) {
    var errorMsg = gettext('A document with this title already exists in this locale.');
    verifyUnique('title', title, document.getElementById('id_title'), form, errorMsg);
  }

  function verifySlugUnique(slug, form) {
    var errorMsg = gettext('A document with this slug already exists in this locale.');
    verifyUnique('slug', slug, document.getElementById('id_slug'), form, errorMsg);
  }

  function verifyUnique(fieldname, value, field, form, errorMsg) {
    if (!field || !form) {
      return;
    }
    field.classList.remove('error');
    var existingList = field.parentNode.querySelector('ul.errorlist');
    if (existingList) {
      existingList.remove();
    }
    var data = {};
    data[fieldname] = value;
    apiFetch(form.dataset.jsonUrl, {
      method: 'GET',
      data: data,
      dataType: 'json'
    })
      .then(function (json) {
        // Success means we found an existing doc
        var docId = form.dataset.documentId;
        if (!docId || (json.id && json.id !== parseInt(docId, 10))) {
          // Collision !!
          field.classList.add('error');
          var list = document.createElement('ul');
          list.className = 'errorlist';
          var item = document.createElement('li');
          item.textContent = errorMsg;
          list.appendChild(item);
          field.parentNode.insertBefore(list, field);
        }
      })
      .catch(function () {
        // A 405 means no existing doc (we're good!); any other error just
        // falls back to server-side validation. Nothing to do either way.
      });
  }
}

// On document edit/translate/new pages, run validation before opening the
// submit modal.
function initPreValidation() {
  var modal = document.getElementById('submit-modal');
  var kbox = modal && modal.kbox;
  if (!kbox) {
    return;
  }
  kbox.updateOptions({
    preOpen: function () {
      var submitBtn = document.querySelector('.btn-submit');
      var form = submitBtn && submitBtn.closest('form');
      if (form && form.checkValidity && !form.checkValidity()) {
        // If form isn't valid, click the modal submit button
        // so the validation error is shown. (I couldn't find a
        // better way to trigger this.)
        var modalSubmit = modal.querySelector('button[type="submit"]');
        if (modalSubmit) {
          modalSubmit.click();
        }
        return false;
      }
      // Add this here because the "Submit for Review" button is
      // a submit button that triggers validation and fails
      // because the modal hasn't been displayed yet.
      var comment = modal.querySelector('#id_comment');
      if (comment) {
        comment.required = true;
      }
      return true;
    },
    preClose: function () {
      // Remove the required attribute so validation doesn't
      // fail after clicking cancel.
      var comment = modal.querySelector('#id_comment');
      if (comment) {
        comment.required = false;
      }
      return true;
    }
  });
}

// The diff revision picker
function initDiffPicker() {
  document.querySelectorAll('div.revision-diff').forEach(function (diff) {
    diff.querySelectorAll('div.picker a').forEach(function (link) {
      link.addEventListener('click', function (ev) {
        ev.preventDefault();
        apiFetch(link.getAttribute('href'), {
          method: 'GET',
          dataType: 'html'
        })
          .then(function (html) {
            var kbox = new KBox(html, {
              modal: true,
              id: 'diff-picker-kbox',
              closeOnOutClick: true,
              destroy: true,
              title: gettext('Choose revisions to compare')
            });
            kbox.open();
            ajaxifyDiffPicker(kbox.kbox.querySelector('form'), kbox, diff);
          })
          .catch(function () {
            alert(gettext('There was an error.'));
          });
      });
    });
  });
}

function ajaxifyDiffPicker(form, kbox, diff) {
  if (!form) {
    return;
  }
  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    apiFetch(form.getAttribute('action'), {
      method: 'GET',
      data: serialize(form),
      dataType: 'html'
    }).then(function (html) {
      kbox.close();
      var template = document.createElement('template');
      template.innerHTML = html.trim();
      diff.replaceWith(template.content);
      initDiffPicker();
      initDiff();
    });
  });
}

export function initReadyForL10n() {
  // Select the "mark as ready" links directly across the whole revision list.
  // The first ".l10n" element is the column header (<th class="l10n">), which
  // has no link - so the old `querySelector('#revision-list .l10n')` grabbed the
  // header and found no links. jQuery's `$('#revision-list .l10n')` matched
  // every cell, so `.find('a.markasready')` found the links.
  var markAsReadyLinks = document.querySelectorAll('#revision-list .l10n a.markasready');
  var modal = document.querySelector('[data-modal-id="ready-for-l10n-modal"]');
  var post_url, checkbox_id;

  markAsReadyLinks.forEach(function (check) {
    check.addEventListener('click', function () {
      // Once a revision is marked ready it gets the "yes" class; ignore
      // further clicks (the old code did this via $().off('click')).
      if (check.classList.contains('yes')) {
        return;
      }
      post_url = check.dataset.url;
      checkbox_id = check.getAttribute('id');
      if (modal) {
        var revtime = modal.querySelector('span.revtime');
        if (revtime) {
          revtime.innerHTML = '(' + check.dataset.revdate + ')';
        }
      }
    });
  });

  if (modal) {
    modal.querySelectorAll('input[type=submit], button[type=submit]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var csrfEl = modal.querySelector('input[name=csrfmiddlewaretoken]');
        var csrf = csrfEl ? csrfEl.value : '';
        if (post_url !== undefined && checkbox_id !== undefined) {
          apiFetch(post_url, {
            method: 'POST',
            data: { csrfmiddlewaretoken: csrf }
          })
            .then(function () {
              var cb = document.getElementById(checkbox_id);
              if (cb) {
                cb.classList.remove('markasready');
                cb.classList.add('yes');
              }
              Modal.closeModal();
            })
            .catch(function () {
              Modal.closeModal();
            });
        }
      });
    });
  }
}

function initNeedsChange() {
  // Hide and show the comment box based on the status of the
  // "Needs change" checkbox. Also, make the textarea required
  // when checked.
  var checkbox = document.getElementById('id_needs_change');
  var comment = document.getElementById('id_needs_change_comment');
  var commentLabel = document.querySelector('label[for="id_needs_change_comment"]');
  var kboxEl = checkbox ? checkbox.closest('.kbox') : null;
  var kbox = kboxEl ? kboxEl.kbox : null;

  if (checkbox) {
    updateComment();
    checkbox.addEventListener('change', updateComment);
  }

  function updateComment() {
    var textarea = comment ? comment.querySelector('textarea') : null;
    var animations = [];
    if (checkbox.checked) {
      if (comment) {
        animations.push(slideDown(comment));
      }
      if (commentLabel) {
        animations.push(slideDown(commentLabel));
      }
      if (textarea) {
        textarea.required = true;
      }
    } else {
      hide(commentLabel);
      hide(comment);
      if (textarea) {
        textarea.required = false;
      }
    }
    if (kbox && kbox.isOpen) {
      // Let the kbox re-measure once the slide has settled.
      Promise.all(animations).then(function () {
        kbox.handleOverflow();
      });
    }
  }
}

function initEditingTools() {
  // Init the show/hide links for editing tools
  document.querySelectorAll('#quick-links .edit a').forEach(function (link) {
    link.addEventListener('click', function (ev) {
      ev.preventDefault();
      var docTabs = document.getElementById('doc-tabs');
      var toggle = docTabs ? slideToggle(docTabs) : Promise.resolve();
      toggle.then(function () {
        document.body.classList.toggle('show-editing-tools');
      });

      if (link.classList.contains('show')) {
        setCookie('show-editing-tools', 1, { path: '/' });
      } else {
        removeCookie('show-editing-tools', { path: '/' });
      }
    });
  });
}

function initCodeMirrorEditor() {
  window.codemirror = true;
  window.highlighting = {};

  var content = document.getElementById('id_content');
  if (!content) {
    return;
  }

  var editor = document.createElement('div');
  editor.id = 'editor';
  var editorWrapper = document.createElement('div');
  editorWrapper.id = 'editor_wrapper';

  var updateHighlightingEditor = function () {
    var currentEditor = window.highlighting.editor;
    if (!currentEditor) {
      return;
    }
    currentEditor.setValue(content.value);
  };
  window.highlighting.updateEditor = updateHighlightingEditor;

  var switchLink = document.createElement('a');
  switchLink.textContent = gettext('Toggle syntax highlighting');
  switchLink.style.textAlign = 'right';
  switchLink.style.cursor = 'pointer';
  switchLink.style.display = 'block';
  switchLink.addEventListener('click', function () {
    if (editorWrapper.style.display === 'block') {
      editorWrapper.style.display = 'none';
      content.style.display = 'block';
    } else {
      updateHighlightingEditor();
      editorWrapper.style.display = 'block';
      content.style.display = 'none';
    }
  });

  var highlightingEnabled = function () {
    return editorWrapper.style.display === 'block';
  };
  window.highlighting.isEnabled = highlightingEnabled;

  editorWrapper.appendChild(editor);
  // Insert editor_wrapper then switch_link immediately after #id_content (each
  // insert goes directly after it, so the final order is content, wrapper,
  // link - matching the old chained jQuery .after().after()). Highlighting is
  // on by default (wrapper visible, textarea hidden).
  content.after(switchLink);
  content.after(editorWrapper);
  editorWrapper.style.display = 'block';
  hide(content);

  document.addEventListener('DOMContentLoaded', function () {
    var cm_editor = CodeMirror(document.getElementById('editor'), {
      mode: { 'name': 'sumo' },
      value: content.value,
      lineNumbers: true,
      lineWrapping: true,
      extraKeys: { 'Ctrl-Space': 'autocomplete' }
    });
    window.highlighting.editor = cm_editor;

    content.addEventListener('keyup', updateHighlightingEditor);
    updateHighlightingEditor();

    cm_editor.on('change', function () {
      if (!highlightingEnabled()) {
        return;
      }
      content.value = cm_editor.getValue();
    });
  }, false);
}

function initFormLock() {
  var doc = document.getElementById('edit-document') || document.getElementById('localize-document');
  var inputs = [];
  if (doc && doc.classList.contains('locked')) {
    inputs = Array.from(doc.querySelectorAll('input:enabled, textarea:enabled'));
    inputs.forEach(function (el) {
      el.disabled = true;
    });
  }
  var unlockButton = document.getElementById('unlock-button');
  if (unlockButton) {
    unlockButton.addEventListener('click', function () {
      inputs.forEach(function (el) {
        el.disabled = false;
      });
      if (doc) {
        doc.classList.remove('locked');
      }
      var lockedWarning = document.getElementById('locked-warning');
      if (lockedWarning) {
        slideUp(lockedWarning, 500);
      }

      // Modify the current url, so we get the right locale.
      var url = window.location.toString().replace(/edit/, 'steal-lock');

      var xhr = new XMLHttpRequest();
      var csrfEl = document.querySelector('#steal-lock-form input[name=csrfmiddlewaretoken]');
      var csrf = csrfEl ? csrfEl.value : null;
      xhr.open("POST", url);
      if (csrf) {
        xhr.setRequestHeader('X-CSRFToken', csrf);
      }
      xhr.send();
    });
  }
}

function initToggleDiff() {
  var diff = document.getElementById('content-diff');
  var contentOrDiff = document.getElementById('content-or-diff');

  if (diff && contentOrDiff) {
    contentOrDiff.appendChild(diff.cloneNode(true));
    var toggle = document.createElement('a');
    toggle.textContent = gettext('Toggle Diff');
    toggle.addEventListener('click', function (e) {
      e.preventDefault();
      contentOrDiff.classList.toggle('content');
      contentOrDiff.classList.toggle('diff');
    });
    contentOrDiff.appendChild(toggle);
  }
}

export function initTranslationDraft() {
  var draftMessage = document.getElementById('draft-message');

  // The submit button bar is rendered twice (top + the #preview-bottom bar
  // revealed after a preview), so there are two ".btn-draft" buttons; wire them
  // all (jQuery's $('.btn-draft') bound the handler to every match).
  document.querySelectorAll('.btn-draft').forEach(function (draftButton) {
    var url = draftButton.dataset.draftUrl;
    draftButton.addEventListener('click', function () {
    var message = gettext('<strong>Draft is saving...</strong>');
    var image = `<img src="${spinnerImg}">`;
    // Merge the fields of all three forms by name (the old code used
    // $.extend on serializeArray() arrays, which merged by index and dropped
    // fields; this sends every field from all three forms).
    var serializeById = function (id) {
      var f = document.getElementById(id);
      return f ? serialize(f) : {};
    };
    var totalData = Object.assign(
      {},
      serializeById('both_form'),
      serializeById('doc_form'),
      serializeById('rev_form')
    );

    if (draftMessage) {
      draftMessage.innerHTML = image + message;
      draftMessage.classList.remove('success', 'error');
      draftMessage.classList.add('info');
      show(draftMessage);
    }
    apiFetch(url, { method: 'POST', data: totalData })
      .then(function () {
        var time = new Date();
        var msg = interpolate(gettext('<strong>Draft has been saved on:</strong> %s'), [time]);
        if (draftMessage) {
          draftMessage.innerHTML = msg;
          draftMessage.classList.remove('info');
          draftMessage.classList.add('success');
          show(draftMessage);
        }
      })
      .catch(function () {
        var msg = gettext('<strong>Error saving draft</strong>');
        if (draftMessage) {
          draftMessage.innerHTML = msg;
          draftMessage.classList.remove('info');
          draftMessage.classList.add('error');
          show(draftMessage);
        }
      });
    });
  });
}

export function initRevisionList() {
  var form = document.querySelector('#revision-list form.filter');
  var searchForm = document.querySelector('.simple-search-form');

  if (!form) {
    return;
  }

  const fragment = document.getElementById('revisions-fragment');

  const initialUrl = window.location.href;
  window.history.replaceState({ url: initialUrl }, '', initialUrl);

  function serializeForm() {
    return new URLSearchParams(new FormData(form)).toString();
  }

  function searchFormOwns(key) {
    return searchForm && searchForm.querySelector(`[name="${key}"]`);
  }

  function updateRevisionList(query, pushState = true) {
    document.querySelectorAll('.loading').forEach(show);

    if (query === undefined) {
      query = serializeForm();
    }

    const baseUrl = form.getAttribute('action');
    const url = new URL(baseUrl, window.location.origin);
    const params = new URLSearchParams(query);

    // Update URL parameters while preserving search form state
    for (let [key, value] of params) {
      url.searchParams.set(key, value);
    }

    if (pushState) {
      window.history.pushState({ url: url.toString() }, '', url);
    }

    if (fragment) {
      fragment.style.opacity = 0;
    }
    apiFetch(url.toString() + (url.search ? '&' : '?') + 'fragment=1', { dataType: 'html' })
      .then(function (data) {
        document.querySelectorAll('.loading').forEach(hide);
        if (fragment) {
          fragment.innerHTML = data;
          fragment.style.opacity = 1;
        }
      });
  }

  // Handle browser back/forward
  window.addEventListener('popstate', function (e) {
    if (e.state) {
      const url = new URL(e.state.url);
      const params = new URLSearchParams();

      // Copy only the parameters that belong to the revision list
      for (let [key, value] of url.searchParams) {
        if (!searchFormOwns(key)) {
          params.set(key, value);
        }
      }

      updateRevisionList(params.toString(), false);
    }
  });

  var timeout;
  function onFilterChange(e) {
    if (!e.target.matches('input, select')) {
      return;
    }
    clearTimeout(timeout);
    timeout = setTimeout(function () {
      updateRevisionList();
    }, 200);

    // Save filter state but exclude pagination
    const currentData = {};
    for (const [name, value] of new FormData(form)) {
      if (name !== 'page') {
        currentData[name] = value;
      }
    }
    sessionStorage.setItem('revision-list-filter', JSON.stringify(currentData));
  }
  form.addEventListener('input', onFilterChange);
  form.addEventListener('change', onFilterChange);

  // Handle pagination clicks
  if (fragment) {
    fragment.addEventListener('click', function (e) {
      const link = e.target.closest('.pagination a');
      if (!link) {
        return;
      }
      e.preventDefault();
      const paginationUrl = new URL(link.getAttribute('href'), window.location.origin);

      // Only take parameters that are not part of the search form
      const params = new URLSearchParams();
      for (let [key, value] of paginationUrl.searchParams) {
        if (!searchFormOwns(key)) {
          params.set(key, value);
        }
      }

      updateRevisionList(params.toString(), true);
    });
  }

  // Remove submit button and prevent form submission
  form.querySelectorAll('button, [type="submit"]').forEach(function (el) {
    el.remove();
  });
  form.addEventListener('keydown', function (e) {
    if (e.which === 13) {
      e.preventDefault();
    }
  });
}

function makeWikiCollapsable() {
  // Hide the TOC
  hide(document.getElementById('toc'));

  // Make sections collapsable
  document.querySelectorAll('#doc-content h1').forEach(function (h1) {
    var sectionElems = [];
    var sibling = h1.nextElementSibling;
    while (sibling) {
      if (sibling.tagName === 'H1') {
        break;
      }
      sectionElems.push(sibling);
      sibling = sibling.nextElementSibling;
    }

    var foldingSection = document.createElement('div');
    foldingSection.classList.add('wiki-section', 'collapsed');
    h1.parentNode.insertBefore(foldingSection, h1);
    foldingSection.appendChild(h1);

    var section = document.createElement('section');
    foldingSection.appendChild(section);

    sectionElems.forEach(function (el) {
      section.appendChild(el);
    });
  });

  // Make the header the trigger for toggling state
  var docContent = document.getElementById('doc-content');
  if (docContent) {
    docContent.addEventListener('click', function (e) {
      var h1 = e.target.closest('h1');
      if (h1 && docContent.contains(h1)) {
        var section = h1.closest('.wiki-section');
        if (section) {
          section.classList.toggle('collapsed');
        }
      }
    });
  }

  // Expand section if deeplinked to it
  if (window.location.hash.length > 1) {
    var target = null;
    try {
      target = document.querySelector(window.location.hash);
    } catch (e) {
      target = null;
    }
    var section = target ? target.closest('.wiki-section') : null;
    if (section) {
      section.classList.remove('collapsed');
    }
  }
}

function initExitSupportFor() {
  var exit = document.getElementById('support-for-exit');
  if (exit) {
    exit.addEventListener('click', function () {
      var supportFor = document.getElementById('support-for');
      if (supportFor) {
        supportFor.remove();
      }
    });
  }
}

function collapsibleContributorTools() {
  const showMoreLink = document.getElementById('show-more-link');
  if (showMoreLink) {
    const collapsibleContent = document.querySelector('.collapsible-content');

    showMoreLink.addEventListener('click', (event) => {
      event.preventDefault();

      collapsibleContent.classList.toggle('expanded');
      showMoreLink.classList.toggle('expanded');
      showMoreLink.textContent = (showMoreLink.classList.contains('expanded')) ? 'Show Less' : 'Show More';
    });
  }
}

init();

var docContentEl = document.getElementById('doc-content');
if (docContentEl && docContentEl.classList.contains('collapsible')) {
  makeWikiCollapsable();
}
