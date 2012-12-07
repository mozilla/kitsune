// Use a global k to share data accross JS files
k = {};

(function () {
    k.LAZY_DELAY = 500;  // delay to lazy loading scripts, in ms
    k.MEDIA_URL = '/media/';
    k.getQueryParamsAsDict = function (url) {
        // Parse the url's query parameters into a dict. Mostly stolen from:
        // http://stackoverflow.com/questions/901115/get-query-string-values-in-javascript/2880929#2880929
        var queryString = '',
            splitUrl,
            urlParams = {},
            e,
            a = /\+/g,  // Regex for replacing addition symbol with a space
            r = /([^&=]+)=?([^&]*)/g,
            d = function (s) { return decodeURIComponent(s.replace(a, " ")); };

        if (url) {
            splitUrl = url.split('?');
            if (splitUrl.length > 1) {
                queryString = splitUrl.splice(1).join('');
            }
        } else {
            queryString = window.location.search.substring(1);
        }

        while (e = r.exec(queryString)) {
           urlParams[d(e[1])] = d(e[2]);
        }
        return urlParams;
    }

    k.getReferrer = function(urlParams) {
        /*
        Get the referrer to the current page. Returns:
        - 'search' - if current url has as=s
        - 'inproduct' - if current url has as=u
        - actual referrer URL - if none of the above
        */
        if (urlParams['as'] === 's') {
            return 'search';
        } else if (urlParams['as'] === 'u') {
            return 'inproduct';
        } else {
            return document.referrer;
        }
    }

    k.getSearchQuery = function(urlParams, referrer) {
        // If the referrer is a search page, return the search keywords.
        if (referrer === 'search') {
            return urlParams['s'];
        } else if (referrer !== 'inproduct') {
            return k.getQueryParamsAsDict(referrer)['q'] || '';
        }
        return '';
    }

    k.unquote = function(str) {
        if (str) {
            // Replace all \" with "
            str = str.replace(/\\\"/g, '"');
            // If a string is wrapped in double quotes, remove them.
            if (str[0] === '"' && str[str.length - 1] === '"') {
                return str.slice(1, str.length - 1);
            }
        }
        return str;
    }

    var UNSAFE_CHARS = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
    };
    k.safeString = function(str) {
        return str.replace(new RegExp('[&<>\'"]', 'g'),
                           function(m) { return UNSAFE_CHARS[m]; });
    };

    k.safeInterpolate = function(fmt, obj, named) {
        if (named) {
            for (var j in obj) {
                obj[j] = k.safeString(obj[j]);
            }
        } else {
            for (var i=0, l=obj.length; i<l; i++) {
                obj[i] = k.safeString(obj[i]);
            }
        }
        return interpolate(fmt, obj, named);
    };


    // Pass CSRF token in XHR header
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
        }
    });

    $(document).ready(function() {
        layoutTweaks();
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
            if ($this.attr('method').toLowerCase() === 'post') {
                if ($this.data('disabled')) {
                    ev.preventDefault();
                } else {
                    $this.data('disabled', true).addClass('disabled');
                }

                function enableForm() {
                    $this.data('disabled', false).removeClass('disabled');
                }

                $this.ajaxComplete(function(){
                    enableForm();
                    $this.unbind('ajaxComplete');
                });

                // Re-enable the form when users leave the page in case they come back.
                $(window).unload(enableForm);
                // Re-enable the form after 5 seconds in case something else went wrong.
                setTimeout(enableForm, 5000);
            }
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

    function layoutTweaks() {
        // Adjust the height of cards to be consistent within a group.
        $('.card-grid').each(function() {
            var $cards = $(this).children('li');
            var max = 0;
            $cards.each(function() {
                var h = $(this).height();
                if (h > max) {
                    max = h;
                }
            });
            $cards.height(max);
        });
    }
})();
