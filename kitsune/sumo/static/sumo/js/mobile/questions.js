(function($) {
    $(function() {
        function refreshAnswers() {
            var width = 0;
            $('.answer-nav > ul > li').each(function() {
                if ($(this).is(':visible')) {
                    width += $(this).outerWidth();
                    width += parseInt($(this).css('marginLeft'));
                    width += parseInt($(this).css('marginRight'));
                }
            });
            $('.answer-nav > ul').css({width: width + 'px'});
        }

        refreshAnswers();

        $('.answer-nav > ul > li').each(function() {
            $(this).on('click', function() {
                $('.answer-nav > ul > li').removeClass('selected');
                $(this).addClass('selected');

                $('#answers > li').removeClass('active');
                $('#answer-' + $(this).data('id')).addClass('active');
            });
        });

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
                refreshAnswers();
            });
        });
    });
}(jQuery));