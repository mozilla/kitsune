/**
 * jQuery LazyLoad
 * Source: http://github.com/pedromenezes/jQuery-lazyload
 *
 * Modifications By: Tanay Gavankar (tgavankar) and Jack Phelan
**/

(function($){
    $.fn.lazyload = function(options){
        var opts = $.extend($.fn.lazyload.defaults, options);
        var elements = this;
        var didScroll = false;
        loaded = elements.length;

        $(window).bind('scroll', function(e){
            didScroll = true;
        });

        loadAboveTheFoldImages(elements, opts, null);

        // Safari doesn't load images until scroll, sometimes
        $(window).trigger('scroll');

        var prevHash = window.location.hash;

        // Anchor links should be preserved
        resetHashPosition();

        var intv = setInterval(function() {
            if(loaded <= 0) {
                $(window).unbind('scroll');
                clearInterval(intv);
                return;
            }
            if(didScroll) {
                didScroll = false;
                if(prevHash != window.location.hash) {
                    // In-page anchor link was clicked, preserve it
                    assocAnchor = window.location.hash;
                    prevHash = window.location.hash;
                }
                else {
                    assocAnchor = null;
                }
                loadedCount = loadAboveTheFoldImages(elements, opts, assocAnchor);
                loaded -= loadedCount;
            }
        }, 250);
        return this;
    };

    $.fn.lazyload.defaults = {threshold: 750};

    function resetHashPosition() {
       if(window.location.hash) {
            // Reset scroll to anchor position if it exists
            window.location.hash = window.location.hash;
        }
    }

    function aboveTheFold(element, options){
        var fold = $(window).height() + $(window).scrollTop();
        return fold >= $(element).offset().top - (options['threshold']);
    };

    $.fn.lazyload.loadOriginalImage = function(element, assocAnchor) {
        if(assocAnchor != null) {
            $(element).load(function() { resetHashPosition(); });
        }
        $(element).attr('src', $(element).data('original-src')).removeData('original-src');
    };

    $.fn.loadnow = function(options) {
        var elements = this;
        elements.each(function() {
            $.fn.lazyload.loadOriginalImage(this);
            $(this).removeClass('lazy');
        });
    }

    function loadAboveTheFoldImages(elements, options, assocAnchor){
        var loaded = 0;
        elements.filter('.lazy').each(function(){
            if ($(this).hasClass('lazy') && aboveTheFold(this, options) &&
                $(this).data('original-src') && $(this).is(":visible")) {
                $.fn.lazyload.loadOriginalImage(this, assocAnchor);
                $(this).removeClass('lazy');
                loaded++;
            }
        });

        return loaded;
    };
})(jQuery);
