$(document).ready(function() {
    // Used for styling.
    $('body').removeClass('no-js').addClass('js');
    var $toc = $('#toc');
    if ($toc.length) {
        // Add icon and collapse it.
        $toc.find('h2')
            .addClass('expando')
            .data('manages', '#toc > ul');
    }

    $('.slidebox h3').addClass('expando').each(function() {
        $(this).data('manages', $(this).parent().children().not('h3'));
    });

    $('select.autosubmit').change(function() {
        $(this).closest('form').submit();
    });

    $('.moz-menu .tab a').click(_pd(function() {
        $('.moz-menu').toggleClass('expand');
        this.blur();
    }));

    $('.desktop-link').click(function() {
        $.cookie('msumo', 'off', {path: '/'});
    });

    if($('#support-for').length > 0) {
        // Set up showfor
        ShowFor.initForTags();
        ShowFor.updateShowforSelectors();
    }

    if($('body').is('.document')) {
        new ArticleHelpfulVote(false);
    }

    $(".expando").each(function() {
        var $trigger = $(this);
        $trigger.click(_pd(function () {
            var $managed = $($trigger.data('manages'));
            $managed.toggleClass("expand");
            if ($managed.hasClass("expand")) {
                $managed.slideDown();
            } else {
                $managed.slideUp();
            }
            $trigger.toggleClass("expand").blur();
        }));
    });

    // This must be called after expando code
    $('.slidebox').each(function() {
        if ($(this).find('.errorlist').length) {
            $(this).closest('.slidebox').find('h3').click();
        }
    });

    if($('body').is('.aaq')) {
        // Prepolate form with user's system info
        new AAQSystemInfo($('#question-form'));
    }
});

function _pd(func) {
    return function(e) {
        e.preventDefault();
        func.apply(this, arguments);
    };
}

// Pass CSRF token in XHR header
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
    }
});
