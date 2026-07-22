import KBox from "sumo/js/kbox";
import AjaxPreview from "sumo/js/ajaxpreview";
import Marky from "sumo/js/markup";
import { apiFetch } from "sumo/js/utils/fetch";
import { serialize } from "sumo/js/utils/dom";

/*
 * forums.js
 * Scripts for the forums app.
 */

function init() {
  Marky.createSimpleToolbar(
    '.editor-tools',
    '#reply-content, #id_content',
    { mediaButton: true });

  new AjaxPreview(document.getElementById('preview'));

  document.querySelectorAll('.post-action a.reply').forEach(function (link) {
    link.addEventListener('click', function () {
      var post = link.dataset.post;
      var postEl = document.getElementById('post-' + post);
      var rawEl = postEl ? postEl.querySelector('div.content-raw') : null;
      var nameEl = postEl ? postEl.querySelector('.display-name') : null;
      var text = rawEl ? rawEl.textContent : '';
      var user = nameEl ? nameEl.textContent : '';
      var reply_text = `''${user} [[#post-${post}|${gettext('said')}]]''\n<blockquote>\n${text}\n</blockquote>\n\n`;
      var textarea = document.getElementById('id_content');

      if (textarea) {
        textarea.value = textarea.value + reply_text;
      }
      return true;
    });
  });

  watchDiscussion();
}

function watchDiscussion() {
  // For a thread on the all discussions for a locale.
  document.querySelectorAll('.watch-form').forEach(function (form) {
    form.addEventListener('click', function (ev) {
      ev.preventDefault();
      apiFetch(form.getAttribute('action'), {
        method: 'POST',
        data: serialize(form),
      })
        .then(function () {
          form.querySelectorAll('a').forEach(function (a) {
            a.classList.toggle('yes');
            a.classList.toggle('no');
          });
          form.querySelectorAll('a.no').forEach(function (a) {
            a.setAttribute('title', gettext('You are not watching this thread'));
          });
          form.querySelectorAll('a.yes').forEach(function (a) {
            a.setAttribute('title', gettext('You are watching this thread'));
          });
        })
        .catch(function () {
          // error growl
        });
    });
  });
}

// Lightbox for all images on click
document.querySelectorAll('.wiki-image').forEach(function (img) {
  // If the image is already linked do not do this
  if (img.closest('a')) {
    return;
  }
  img.addEventListener('click', function (ev) {
    ev.preventDefault();
    var imgUrl = img.getAttribute('src');
    var image = new Image();
    var html = '<div><img class="loading" /></div>';
    var kbox = new KBox(html, {
      modal: true,
      title: gettext('Image Attachment'),
      id: 'wiki-image-kbox',
      destroy: true,
    });
    kbox.open();

    function setWidth() {
      var box = document.getElementById('wiki-image-kbox');
      if (box) {
        box.style.width = image.width + 'px';
        var boxImg = box.querySelector('img');
        if (boxImg) {
          boxImg.classList.remove('loading');
          boxImg.setAttribute('src', imgUrl);
        }
      }
      kbox.setPosition();
    }

    image.onload = setWidth;
    image.src = imgUrl;
    if (image.width) {
      setWidth();
    }
  });
});

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
