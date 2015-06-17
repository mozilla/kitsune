$(document).ready(function() {
    // initiate tabs
    var tabs = $('#search-tabs').tabs(),
        cache_search_date = $('.showhide-input');

    $("#tab-wrapper form").submit(function() {
        $('input.auto-fill').each(function() {
            if ($(this).val() == $(this).attr('placeholder')) {
                $(this).val('');
            }
        });
    });

    $('.datepicker').datepicker();
    $('.datepicker').attr('readonly', 'readonly').css('background', '#ddd');

    $('select', cache_search_date).change(function () {
        if ($(this).val() == 0) {
            $('input', $(this).parent()).hide();
        } else {
            $('input', $(this).parent()).show();
        }
    }).change();

    switch(parseInt($('#where').text(), 10)) {
        case 4:
            tabs.tabs({active: 2});
            break;
        case 2:
            tabs.tabs({active: 1});
            break;
        case 1:
        default:
            tabs.tabs({active: 0});
    }
});
