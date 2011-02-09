(function() {
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

})();

function _pd(func) {
    return function(e) {
        e.preventDefault();
        func.apply(this, arguments);
    };
}
