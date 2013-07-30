(function($) {
    "use strict";

    $(document).ready(function() {
      $('#media-type-select').on('change', function() {
        window.location = $(this).val();
      });
    });

    var CONSTANTS = {
            maxFilenameLength: 70,  // truncated on display, if longer
            // the remainder are set by input name, not file type
            messages: {},
            extensions: {
                file: ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff']},
            max_size: {
                file: $('#gallery-upload-modal').data('max-image-size')
            }
        };

    CONSTANTS.messages['server'] = gettext('Could not upload file. Please try again later.');
    CONSTANTS.messages['file'] = {
        'server': CONSTANTS.messages['server'],
        'invalid': gettext('Invalid image. Please select a valid image file.'),
        'cancelled': gettext('Upload cancelled. Please select an image file.'),
        'deleted': gettext('File deleted. Please select an image file.'),
        'del': gettext('Delete this image')};

    // Save all initial values of input details:
    CONSTANTS.messages.initial = {};
    $('#gallery-upload-modal .upload-media').each(function () {
        var $self = $(this);
        var type = $self.find('input').attr('name'),
            details = $self.find('.details').html();
        CONSTANTS.messages.initial[type] = details;
    });

    // jQuery helpers to show/hide content, provide flexibility in animation.
    $.fn.showFade = function() {
        this.removeClass('off').addClass('on');
        return this;
    };
    $.fn.hideFade = function() {
        this.removeClass('on').addClass('off');
        return this;
    };

    /*
     * Tiny helper function returns true/false depending on whether x is in
     * array arr.
     */
    function in_array(needle, haystack) {
        return (-1 !== Array.prototype.indexOf.call(haystack, needle));
    }

    /*
     * This is the core of the gallery upload process.
     *
     * Summary:
     * init: initialize DOM events, dispatch on draft vs new upload
     * validateForm: prevent form submission if data is not valid
     * isValidFile: boolean result for each type of file, checks size and
     *              extenson
     * startUpload: validates before upload and initiates progress
     * uploadComplete: once upload is done, dispatch to success or error
     * uploadSuccess: successful upload is shown in a preview
     * uploadError: if an error occured, show a message and chance to re-upload
     * deleteUpload: for already uploaded files, send delete request and
     *               show the file <input>
     * cancelUpload: cancel an upload that is in progress
     * draftSetup: show/hide fields according to an existing draft
     *             (image drafts take precedence)
     * modalClose: when closing the modal, delete the draft and reset (below)
     * modalReset: clean up the form in anticipation of a complete do-over
     */
    var GalleryUpload = {
        forms: {$image: $('#gallery-upload-image')},
        $modal: $('#gallery-upload-modal'),
        // some mapping here for what to show/hide and when
        /*
         * -- check if a draft exists and open the modal if so
         * -- set up DOM events: selecting media type, click to cancel upload
         *    ajax uploads, require metadata, bind modal close event
         */
        init: function() {
            var self = this;
            self.forms.$image.showFade();

            // Bind cancel upload event.
            $('.progress a', self.$modal).click(function cancelUpload(ev) {
                var type = $(this).attr('class');
                ev.preventDefault();
                self.cancelUpload($(this));
                self.setInputError($(this).closest('.upload-form')
                                          .find('input[name="' + type + '"]'),
                                   'cancelled');
                return false;
            });

            // Bind ajax uploads for inputs
            $('input[type="file"]', self.$modal).each(function() {
                var $file = $(this), $form = $file.closest('.upload-form');
                $file.ajaxSubmitInput({
                    url: $form.data('post-url'),
                    beforeSubmit: function($input) {
                        if (!self.isValidFile($file)) {
                            self.uploadError($file, 'invalid');
                            return false;
                        }
                        return self.startUpload($file);
                    },
                    onComplete: function($input, iframeContent, options) {
                        $input.closest('form')
                            .trigger('ajaxComplete')[0].reset();
                        self.uploadComplete($file, iframeContent, options);
                    }
                });
            });

            // Deleting uploaded files sends ajax request.
            jQuery.fn.makeCancelUpload = function(options) {
                var $input = this,
                    field_name = $input.data('name');
                if (!$input.is('input')) {
                    return $input;
                }
                if ($input.length > 1) {
                    // Apply to each individually.
                    $input.each(function() {
                        $(this).makeCancelUpload();
                    });
                    return $input;
                }

                var $form = $input.wrap('<form class="inline" method="POST" ' +
                                        'action=""/>').closest('form');
                // Also send the csrf token.
                $form.append($('input[name="csrfmiddlewaretoken"]')
                     .first().clone());

                $input.click(function deleteField(ev) {
                    ev.preventDefault();
                    self.deleteUpload($input);
                    return false;
                });
            }

            // Metadata should be required.
            self.$modal.find('.metadata input,.metadata textarea')
                       .attr('required', 'required');

            // Closing the modal with top-right X cancels upload drafts
            self.$modal.delegate('a.close', 'click', function(e) {
                self.$modal.find('input[name="cancel"]:last').click();
            });

            // Submitting the form should call for validation first.
            function validateSubmit(ev) {
                if (!self.validateForm($(ev.target))) {
                    ev.preventDefault();
                    return false;
                }
            }
            self.forms.$image.find('input[name="upload"]').click(validateSubmit);


            if (self.forms.$image.hasClass('draft')) {
                // draft
                self.draftSetup();
            } else {
                // not draft
                self.modalReset();
            }
        },
        /*
         * Validates the entire upload form before publishing a draft.
         */
        validateForm: function($input) {
            var self = this,
                $form = $input.closest('.upload-form');
            // An image must be uploaded
            if ($form[0] == self.forms.$image[0] &&
                $form.find('.on input[type="file"]').length) {
                return false;
            }
            // Metadata must be filled out
            if (!Modernizr.input.required &&
                (!$form.find('input[name="title"]').val() ||
                 !$form.find('textarea[name="description"]').val() ||
                 !$form.find('select[name="locale"]').val())) {
                return false;
            }

            return true;
        },
        /*
         * Validates uploaded file meets criteria in mapping:
         * -- correct extension
         * -- enable submit button if form is ready to submit
         * TODO: test in IE/no-file-API-supported browser
         */
        isValidFile: function ($input) {
            var file = $input[0].files[0],
                type = $input.attr('name');
            var file_ext = file.name.split(/\./).pop().toLowerCase();
            return (in_array(file_ext, CONSTANTS.extensions[type]) &&
                    file.size < CONSTANTS.max_size[type]);
        },
        /*
         * Fired when upload starts, if isValidFile returns true
         * -- hide the file input
         * -- show progress
         * -- show metadata
         * -- disable submit buttons (happens automatically)
         * -- return the truncated filename for later use
         */
        startUpload: function($input) {
            var $form = $input.closest('.upload-form'),
                filename = $input.val().split(/[\/\\]/).pop(),
                $progress = $('.progress', $form)
                    .filter('.' + $input.attr('name'));
            // truncate filename
            if (filename.length > CONSTANTS.maxFilenameLength) {
                filename = filename.substr(0, CONSTANTS.maxFilenameLength) +
                           '...';
            }
            $form.find('.upload-media.' + $input.attr('name')).hideFade();
            var message = interpolate(gettext('Uploading "%s"...'), [filename]);
            $progress.filter('.row-right').find('span').text(message);
            $progress.showFade();
            $form.find('.metadata').show();
            return {filename: filename};
        },
        /*
         * Dispatches to uploadError or uploadSuccess depending on the
         * response received from the ajax request.
         */
        uploadComplete: function($input, iframeContent, options) {
            if (!iframeContent) {
                return;
            }
            var iframeJSON, self = this;
            try {
                iframeJSON = $.parseJSON(iframeContent);
            } catch(err) {
                self.uploadError($input, 'server');
            }

            var upStatus = iframeJSON.status;

            if (upStatus !== 'success') {
                self.uploadError($input, 'invalid');
                return false;
            }
            // Success!
            self.uploadSuccess($input, iframeJSON, options.filename);
        },
        /*
         * Fired after upload is complete, if isValidFile is true, and server
         * returned succes.
         * -- hide progress
         * -- generate image preview
         * -- create cancel button and bind its click event
         */
        uploadSuccess: function($input, iframeJSON, filename) {
            var type = $input.attr('name'),
                $form = $input.closest('.upload-form'),
                $cancel_btn = $('.upload-action input[name="cancel"]', $form),
                $content, attrs = {},
                $preview_area,
                upFile = iframeJSON.file;
            var message = CONSTANTS.messages[type].del;

            // Upload is no longer in progress.
            $form.find('.progress.' + type).hideFade();

            // generate preview
            if (type === 'file') {
                // create thumbnail
                $content = $('<img/>')
                    .attr({alt: upFile.name, title: upFile.name,
                           width: upFile.width, height: upFile.height,
                           src: upFile.thumbnail_url})
                    .wrap('<div class="preview-' + type + '"/>').parent();
            }
            $preview_area = $('.preview.' + type, $form);
            $preview_area.filter('.row-right').html($content);
            // Create cancel button.
            attrs['data-action'] = $cancel_btn.data('action') +
                                       '?field=' + type;
            attrs['data-name'] = type;
            $cancel_btn.clone().val(message).attr(attrs)
                       .removeClass('kbox-cancel')
                       .appendTo($preview_area.filter('.row-right'))
                       .makeCancelUpload();
            // Show the preview area and make it a draft
            $preview_area.showFade();
            $form.addClass('draft');
        },
        /*
         * Little helper function to set an error next to the file input.
         * Takes the file $input and a reason.
         */
        setInputError: function($input, reason) {
            var type = $input.attr('name');
            var message = CONSTANTS.messages[type][reason];
            var $row_input = $('.upload-media.row-right.' + type);
            $row_input.find('div.details').addClass('error')
                  .html(message);
        },
        /*
         * Fired if isValidFile is false or server returned failure.
         * -- hide progress (i.e. click the cancel button)
         * -- show an error message
         */
        uploadError: function($input, reason) {
            var self = this,
                type = $input.attr('name');
            // Cancel existing upload.
            $('.progress.' + type).find('a.' + type).click();
            // Show an error message.
            self.setInputError($input, reason);
        },
        /*
         * Fired when deleting an uploaded image.
         * -- hide preview of image
         * -- send off an ajax request to remove the uploaded file
         * -- show file input along with a message
         */
        deleteUpload: function($input) {
            var self = this,
                $cancelForm = $input.closest('form'),
                $mediaForm = $input.closest('.upload-form'),
                type = $input.data('name');
            // Clean up all the preview and progress information.
            $mediaForm.find('.preview.' + type).hideFade()
                      .filter('.row-right').html('');

            // Send ajax request over to remove file.
            $.ajax({
                url: $input.data('action'),
                type: 'POST',
                data: $cancelForm.serialize(),
                dataType: 'json'
                // Ignore the response, nothing to do.
            });
            self.setInputError($mediaForm.find('input[name="' + type + '"]'),
                               'deleted');
            self._reUpload($mediaForm, type);
        },
        /*
         * Fired after user closes modal or clicks to cancel an upload in
         * progress.
         * -- hide the progress
         * -- show the file input
         */
        cancelUpload: function($a) {
            var self = this,
                type = $a.attr('class'),
                $form = $a.closest('form');
            var $input = $form.find('input[name="' + type + '"]');
            var form_target = $input.closest('form').attr('target');
            $('iframe[name="' + form_target + '"]')[0].src = null;
            $form.find('.progress.' + type).hideFade();
            self._reUpload($form, type);
        },
        /*
         * Abstracts common code for re-uploading image
         * -- if no other uploads are in progress and none have completed,
         *    hide the metadata fields
         * -- show the file input
         */
        _reUpload: function($form, type) {
            // If nothing else is being or has been uploaded, hide the metadata
            // and enable the upload input.
            if (!$form.find('.progress').hasClass('on') &&
                !$form.find('.preview').hasClass('on')) {
                $form.find('.metadata').hide();
                $form.removeClass('draft');
            }
            // finally, show the input again
            $form.find('.upload-media.' + type).showFade();
        },
        /*
         * If there is a draft, this will be fired off from init()
         * -- hide fields that are already set, use the data-[field] on the
         *    form
         * -- show metadata
         * -- make cancel buttons work
         * -- disable changing upload type
         */
        draftSetup: function() {
            var self = this;
            self.$modal.find('.progress').hideFade();
            var $uploads = self.$modal.find('input[type="file"]');
            $uploads.each(function () {
                var $self = $(this);
                var type = $self.attr('name'),
                    $form = $self.closest('.upload-form');
                if ($form.data(type)) {
                    $form.find('.upload-media.' + type).hideFade();
                } else {
                    $form.find('.upload-media.' + type).showFade();
                }
            });
            if (self.forms.$image.hasClass('draft')) {
                self.forms.$image.find('.upload-media').hideFade();
            }
            self.$modal.find('input[name="cancel"]').not('.kbox-cancel')
                       .makeCancelUpload();
        },
        /*
         * Fired when user closes modal.
         * -- delete selected draft or image
         * -- call modalReset
         */
        modalClose: function() {
            var self = this,
                csrf = $('input[name="csrfmiddlewaretoken"]').first().val(),
                $input = $('.upload-action input[name="cancel"]', self.$modal);
            if (self.$modal.find('.draft').length) {
                // If there's a draft to cancel.
                $.ajax({
                    url: $input.data('action'),
                    type: 'POST',
                    data: 'csrfmiddlewaretoken=' + csrf,
                    dataType: 'json'
                    // Ignore the response, nothing to do.
                });
            }
            self.modalReset();
        },
        /*
         * Fired on modal close.
         * -- reset all form elements and clean up
         */
        modalReset: function() {
            var self = this,
                $uploads = self.$modal.find('.upload-media');
            self.$modal.find('.draft').removeClass('draft');
            // Hide metadata
            self.$modal.find('.metadata').hide();
            // Clean up all the preview and progress information.
            self.$modal.find('.progress,.preview').hideFade();
            self.$modal.find('.preview.row-right').html('');
            self.$modal.find('.progress.row-right span').html('');
            // Show all the file inputs with default messages.
            $uploads.filter('.row-right').each(function () {
                var $input = $(this).find('input[type="file"]'),
                    type = $input.attr('name');
                $input.closest('form')[0].reset();
                $(this).find('.details').html(CONSTANTS.messages.initial[type]);
            }).find('.error').removeClass('error');
            $uploads.showFade();
            // Cancel all uploads in progress.
            self.$modal.find('.progress a').each(function() {
                self.cancelUpload($(this));
            });
            // Reset the forms.
            self.forms.$image[0].reset();
        }
    };

    // Initialize GalleryUpload and kbox
    GalleryUpload.init();
    function preClose() {
        GalleryUpload.modalClose();
        return true;
    }

    var kbox = $('#gallery-upload-modal').kbox({preClose: preClose});

    // Open modal window from media page
    if (document.location.hash === '#upload' ||
        $('#gallery-upload-type').hasClass('draft')) {
        $('#btn-upload').click();
    }

})(jQuery);
