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

        loadAboveTheFoldImages(elements, opts);

        var intv = setInterval(function() {
            if(loaded <= 0) {
                $(window).unbind('scroll');
                clearInterval(intv);
                return;
            }
            if(didScroll) {
                didScroll = false;
                loaded -= loadAboveTheFoldImages(elements, opts);
            }
        }, 250);
        return this;
    };

    $.fn.lazyload.defaults = {threshold: 750};

    function aboveTheFold(element, options){
        var fold = $(window).height() + $(window).scrollTop();
        return fold >= $(element).offset().top - (options['threshold']);
    };

    $.fn.lazyload.loadOriginalImage = function(element){
        $(element).attr('src', $(element).data('original-src')).removeData('original-src');
    };

    function loadAboveTheFoldImages(elements, options){
        var loaded = 0;
        elements.filter('.lazy').each(function(){
            if ($(this).hasClass('lazy') && aboveTheFold(this, options) &&
                $(this).data('original-src') && $(this).is(":visible")) {
                $.fn.lazyload.loadOriginalImage(this);
                $(this).removeClass('lazy');
                loaded++;
            }
        });
        return loaded;
    };
})(jQuery);
