/* globals $:false, gettext:false, KBox:false, interpolate:false */
$(document).ready(function () {
  var UPLOAD = {
    max_filename_length: 80,  // max filename length in characters
    error_title_up: gettext('Error uploading image'),
    error_title_del: gettext('Error deleting image'),
    error_login: gettext('Please check you are logged in, and try again.')
  };

  function dialogSet(inner, title) {
    var kbox = new KBox($('<p/>').text(inner), {
      title: title,
      destroy: true,
      closeOnOutClick: true,
      modal: true,
      id: 'upload-dialog',
      container: $('body')
    });
    kbox.open();
  }

  $('input.delete', 'div.attachments-list').each(function () {
    var $form = $(this).closest('form');
    $(this).wrapDeleteInput({
      error_title_del: UPLOAD.error_title_del,
      error_login: UPLOAD.error_login,
      onComplete: function() {
        $form.trigger('ajaxComplete');
      }
    });
  });

  // Upload a file on input value change
  $('div.attachments-upload input[type="file"]').each(function() {
    var $form = $(this).closest('form');
    $form.removeAttr('enctype');
    $(this).ajaxSubmitInput({
      url: $(this).closest('.attachments-upload').data('post-url'),
      beforeSubmit: function($input) {
        var $divUpload = $input.closest('.attachments-upload'),
        $options = {
          progress: $divUpload.find('.upload-progress'),
          add: $divUpload.find('.add-attachment'),
          adding: $divUpload.find('.adding-attachment'),
          loading: $divUpload.find('.uploaded')
        };

        // truncate filename
        $options.filename = $input.val().split(/[\/\\]/).pop();
        if ($options.filename.length > UPLOAD.max_filename_length) {
          $options.filename = $options.filename
          .substr(0, UPLOAD.max_filename_length - 3) + '...';
        }

        $options.add.hide();
        $options.adding.text(interpolate(gettext('Uploading "%s"...'),
        [$options.filename]))
        .show();
        $options.loading.removeClass('empty');
        $options.progress.addClass('show');
        return $options;
      },
      onComplete: function($input, iframeContent, $options) {
        var iframeJSON;
        var upFile;
        var $thumbnail;
        var upStatus;

        $input.closest('form')[0].reset();
        if (!iframeContent) {
          return;
        }

        try {
          iframeJSON = $.parseJSON(iframeContent);
        } catch(err) {
          if (err.substr(0, 12) === 'Invalid JSON') {
            dialogSet(UPLOAD.error_login, UPLOAD.error_title_up);
          }
        }

        upStatus = iframeJSON.status;

        $options.progress.removeClass('show');
        if (upStatus === 'success') {
          upFile = iframeJSON.file;
          // HTML decode the name.
          upFile.name = $('<div/>').html(upFile.name).text();
          $thumbnail = $('<img/>')
          .attr({
            alt: upFile.name, title: upFile.name,
            width: upFile.width, height: upFile.height,
            src: upFile.thumbnail_url
          })
          .removeClass('upload-progress')
          .wrap('<a class="image" href="' + upFile.url + '"></a>')
          .closest('a')
          .wrap('<div class="attachment"></div>')
          .closest('div')
          .addClass('attachment')
          .insertBefore($options.progress);
          $thumbnail.prepend(
            '<input type="submit" class="delete" data-url="' +
            upFile.delete_url + '" value="&#x2716;"/>');
          $thumbnail.children().first().wrapDeleteInput({
            error_title_del: UPLOAD.error_title_del,
            error_login: UPLOAD.error_login,
            onComplete: function() {
              $form.trigger('ajaxComplete');
            }
          });
        } else {
          dialogSet(iframeJSON.message, UPLOAD.error_title_up);
        }

        $options.adding.hide();
        $options.add.show();

        $form.trigger('ajaxComplete');
      }
    });
  });

  // hijack the click on the thumb and open modal kbox
  function initImageModal() {
    $('article').on('click', '.attachments-list a.image', function(ev) {
      ev.preventDefault();
      var imgUrl = $(this).attr('href'),
      image = new Image(),
      html = '<div><img class="loading" /></div>',
      kbox = new KBox(html, {
        modal: true,
        title: gettext('Image Attachment'),
        id: 'image-attachment-kbox',
        destroy: true
      });
      kbox.open();

      function setWidth() {
        $('#image-attachment-kbox').width(image.width)
        .find('img').removeClass('loading').attr('src', imgUrl);
        kbox.setPosition();
      }

      image.onload = setWidth;
      image.src = imgUrl;
      if (image.width) {
        setWidth();
      }
    });
  }
  initImageModal();

  // Workaround to IE6's lack of div:hover support
  if ($.browser.msie && $.browser.version === '6.0') {
    $('div.attachments-upload').delegate('div.attachment', 'hover',
    function(ev) {
      if (ev.type === 'mouseover' || ev.type === 'mouseenter') {
        $(this).addClass('hover');
      } else {
        $(this).removeClass('hover');
      }
    });
  }
});
