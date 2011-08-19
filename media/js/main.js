// Use a global k to share data accross JS files
k = {};

(function () {
    k.LAZY_DELAY = 500;  // delay to lazy loading scripts, in ms
    k.MEDIA_URL = '/media/';

    // Pass CSRF token in XHR header
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
        }
    });

    $(document).ready(function() {
        /* Focus form field when clicking on error message. */
        $('#content ul.errorlist a').click(function () {
                $($(this).attr('href')).focus();
                return false;
            });

        if ($('body').data('readonly')) {
            $forms = $('form[method=post]');
            $forms.find('input, button, select, textarea').attr('disabled', 'disabled');
            $forms.find('input[type=image]').css('opacity', .5);
            $('div.editor-tools').remove();
        }

        $('input[placeholder]').placeholder();

        initAutoSubmitSelects();
        disableFormsOnSubmit();
        lazyLoadScripts();
    });

    /*
     * Initialize some selects so that they auto-submit on change.
     */
    function initAutoSubmitSelects() {
        $('select.autosubmit').change(function() {
            $(this).closest('form').submit();
        });
    }

    /*
     * Disable forms on submit to avoid multiple POSTs when double+ clicking.
     * Adds `disabled` CSS class to the form for optionally styling elements.
     *
     * NOTE: We can't disable the buttons because it prevents their name/value
     * from being submitted and we depend on those in some views.
     */
    function disableFormsOnSubmit() {
        $('form').submit(function(ev) {
            var $this = $(this);
            if ($this.data('disabled')) {
                ev.preventDefault();
            } else {
                $this.data('disabled', true).addClass('disabled');
            }

            $this.ajaxComplete(function(){
                $this.data('disabled', false).removeClass('disabled');
                $this.unbind('ajaxComplete');
            });
        });
    }

    /*
     * This lazy loads our jQueryUI script.
     */
    function lazyLoadScripts() {
        var scripts = ['js/libs/jqueryui-min.js'],
            styles = [],  // was: ['css/jqueryui/jqueryui-min.css']
                          // turns out this messes with search
            i;

        // Don't lazy load scripts that have already been loaded
        $.each($('script'), function () {
            var this_src = $(this).attr('src');
            if (!this_src) return ;
            remove_item(scripts, this_src);
        });

        // Don't lazy load stylesheets that have already been loaded
        $.each($('link[rel="stylesheet"]'), function () {
            remove_item(styles, $(this).attr('href'));
        });

        setTimeout(function lazyLoad() {
            for (i in scripts) {
                $.get(k.MEDIA_URL + scripts[i]);
            }
            for (i in styles) {
                $('head').append(
                    '<link rel="stylesheet" type="text/css" href="' +
                    k.MEDIA_URL + styles[i] + '">');
            }
        }, k.LAZY_DELAY);
    }

    /*
     * Remove an item from a list if it matches the substring match_against.
     * Caution: modifies from_list.
     * E.g. list = ['string'], remove_item(list, 'str') => list is [].
     */
    function remove_item(from_list, match_against) {
        match_against = match_against.toLowerCase();
        for (var i in from_list) {
            if (match_against.indexOf(from_list[i]) >= 0) {
                from_list.splice(i, 1);
            }
        }
    }

    /**
     * Remove messages 20 seconds after mousemove.
     */
    function removeMessagesList() {
        var $msgs = $('ul.user-messages');
        if ($msgs.length) {
            function moveListener () {
                setTimeout(function() {
                    $msgs.slideUp('fast', function() {
                        $msgs.remove();
                    });
                }, 20000);
            }
            $(document).one('mousemove', moveListener);
        }
    }
    $(document).ready(removeMessagesList);
})();
