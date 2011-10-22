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

        $(window).bind('scroll', function(e){
            loadAboveTheFoldImages(elements, opts);
        });

        loadAboveTheFoldImages(elements, opts);
        return this;
    };

    $.fn.lazyload.defaults = {threshold: 30};

    function aboveTheFold(element, options){
        var fold = $(window).height() + $(window).scrollTop();
        return fold >= $(element).offset().top - (options['threshold']);
    };

    $.fn.lazyload.loadOriginalImage = function(element){
        $(element).attr('src', $(element).attr('original-src')).removeAttr('original-src');
    };

    function loadAboveTheFoldImages(elements, options){
        elements.each(function(){
            if (aboveTheFold(this, options) && ($(this).attr('original-src')) && $(this).is(":visible")){
                $.fn.lazyload.loadOriginalImage(this);
            }
        });
    };
})(jQuery);
