(function($) {
    var $body = $('body');

    if ($('#support-for').length > 0) {
        // Set up showfor
        ShowFor.initForTags();
    }

    if ($body.is('.document')) {
        var focusOn = window.location.hash;
        var $voteForm = $('.vote-bar form');
        var $voteButtons = $voteForm.find('input[type="submit"], .btn[data-type="submit"]');

        window.k.AjaxForm($voteForm, {
            removeForm: true,
            afterComplete: function() {
                window.k.AjaxForm($('.vote-bar form'), {
                    removeForm: true,
                    validate: function(data) {
                        if (data['unhelpful-reason'] === 'other') {
                            if (data['comment'].length < 1) {
                                return false;
                            }
                        }
                        return true;
                    }
                });
            }
        });

        $('.vote-bar').on('change', 'input[type="radio"]', function() {
            var $ul = $(this).closest('ul');
            $ul.children().each(function(){
               $(this).removeClass('checked');
            });
            if (this.checked) {
                $(this).closest('li').addClass('checked');
            }
        });

        $('.vote-bar').on('input', '#unhelpful-survey textarea', function() {
            var $survey = $(this).closest('#unhelpful-survey');
            var $commentCount = $survey.find('#remaining-characters');
            var $counter = $commentCount.closest('.character-counter');

            if (!$commentCount.data('max')) {
                $commentCount.data('max', parseInt($commentCount.text()));
            }

            var count = $(this).val().length;
            var remaining = $commentCount.data('max') - count;

            $commentCount.html(remaining);

            if (remaining < 0) {
                $counter.addClass('too-long');
            } else {
                $counter.removeClass('too-long');
            }
        });

        function killFocus() {
            focusOn = null;
        }

        function refocus(id) {
            var scrollable = $('#content').closest('.scrollable')[0];
            var scrollTo = $(id).position().top + scrollable.scrollTop;
            $(document).off('scroll', killFocus);
            scrollable.scrollTop = scrollTo;
            $(document).on('scroll', killFocus);
        }

        $('#toc').on('click', 'a', function(e) {
            focusOn = $(this).attr('href')
            refocus(focusOn);
            return false;
        });

        $('img.lazy').on('load', function() {
            if (focusOn) {
                refocus(focusOn);
            }
        });
    }

    $('img.lazy').lazyload({bindTo: $('#page > .scrollable')});
})(jQuery);
