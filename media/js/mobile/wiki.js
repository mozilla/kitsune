(function($){
    var $body = $('body');

    if ($('#support-for').length > 0) {
        // Set up showfor
        ShowFor.initForTags();
    }

    function handleSubmit() {
        var $this = $(this);
        var $form = $this.closest('form');
        var $buttons = $form.find('input[type="submit"], .btn[data-type="submit"]');
        var formDataArray = $form.serializeArray();
        var data = {};

        $buttons.attr('disabled', 'disabled');

        for (i = 0, l = formDataArray.length; i < l; i++) {
            data[formDataArray[i].name] = formDataArray[i].value;
        }
        data[$this.attr('name')] = $this.val();

        $.ajax({
            url: $form.attr('action'),
            type: 'POST',
            data: data,
            dataType: 'json',
            success: function(data) {
                if (data.survey) {
                    $form.after(data.survey);
                } else {
                    $form.after($('<p></p>').html(data.message));
                }
                $form.remove();
                $buttons.removeAttr('disabled');
            },
            error: function() {
                var msg = gettext('There was an error submitting your vote.');
                $form.after($('<p></p>').html(msg));
                $buttons.removeAttr('disabled');
                $form.removeClass('busy');
            }
        });

        return false;
    }

    if ($body.is('.document')) {
        var $voteForm = $('.vote-bar form');
        var $voteButtons = $voteForm.find('input[type="submit"], .btn[data-type="submit"]');

        $voteButtons.on('click', handleSubmit);

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

        $('.vote-bar').on('click', '#unhelpful-survey input[type="submit"], #unhelpful-survey .btn[data-type="submit"]', handleSubmit);
    }

    $('img.lazy').lazyload();
})(jQuery)
