import "sumo/js/libs/jquery.lazyload";

/*
 * Wiki content previews - ajaxified.
 */

export default function AjaxPreview(el, options) {
  /* Args:
   * el - The button/link DOM element that triggers the preview
   * options - dict of options
   *      previewUrl - url to POST the content and get a preview
   *      contentElement - DOM element or selector that input content
   *      previewElement - DOM element or selector to insert the preview
   *      changeHash - Change document.location.hash to the id of
   *                   previewElemnt (default: true)
   */
  AjaxPreview.prototype.init.call(this, el, options);
}

(function($) {

  'use strict';

  AjaxPreview.prototype = {
    init: function(el, options) {
      var self = this,
        $btn = $(el),
        o = options || {},
        previewUrl = o.previewUrl || $btn.data('preview-url'),
        $preview = (o.previewElement && $(o.previewElement)) ||
                   $('#' + $btn.data('preview-container-id')),
        $content = (o.contentElement && $(o.contentElement)) ||
                   $('#' + $btn.data('preview-content-id')),
        csrftoken = $btn.closest('form')
        .find('input[name=csrfmiddlewaretoken]').val(),
        slug = ($btn.closest('form').find('input[name=slug]').val()) ||
                window.location.pathname,
        locale = $btn.closest('form').find('[name=locale]').val(),
        changeHash = o.changeHash === undefined ? true : o.changeHash;

      $btn.on('click', function(e) {
        e.preventDefault();
        $(this).attr('disabled', 'disabled');
        $(self).trigger('get-preview');
      });

      // Trying to make this event driven for easier testability.
      $(self).on('get-preview', function(e) {
        $.ajax({
          url: previewUrl,
          type: 'POST',
          data: {
            content: $content.val(),
            slug: slug,
            locale: locale,
            csrfmiddlewaretoken: csrftoken
          },
          dataType: 'html',
          success: function(html) {
            $(self).trigger('show-preview', [true, html]);
          },
          error: function(xhr, status, err) {
            console.log(err);
            var msg = gettext('There was an error generating the preview.');
            $(self).trigger('show-preview', [false, msg]);
          }
        });
      });

      $(self).on('show-preview', function(e, success, html) {
        $preview.html(html);
        if ($.fn.lazyload) {
          $preview.find('img.lazy').lazyload();
        }
        if (changeHash) {
          document.location.hash = $preview.attr('id');
        }
        $btn.removeAttr('disabled');
        $(self).trigger('done', [success]);
      });
    }
  };

})(jQuery);
