(function($) {
    $(function() {
        var width = 0;
        $('.answer-nav > ul > li').each(function() {
            width += $(this).outerWidth();
            width += parseInt($(this).css('marginLeft'));
            width += parseInt($(this).css('marginRight'));

            $(this).on('click', function() {
                $('.answer-nav > ul > li').removeClass('selected');
                $(this).addClass('selected');

                $('#answers > li').removeClass('active');
                $('#answer-' + $(this).data('id')).addClass('active');
            });
        });
        $('.answer-nav > ul').css({width: width + 'px'});

        $('.answer-tabs > li').each(function(){
            $(this).on('click', function(){
                $(this).siblings().removeClass('selected').each(function() {
                    var className = $(this).data('class');
                    if (className) {
                        $(this).closest('.answer-bar').removeClass(className);
                    }
                });
                var className = $(this).data('class');
                if (className) {
                    $(this).closest('.answer-bar').addClass(className);
                }
                $(this).addClass('selected');
            });
        });
    });
}(jQuery));