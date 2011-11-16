(function($) {
    var html = '<a style="width:400px;height:32px;vertical-align:middle;text-align:center;background-color:#000;position:absolute;z-index:5555;top:40px;left:10px;background-image:url(%simg/mozillaorg_censorship_wht.png);background-position:center center;background-repeat:no-repeat;text-indent:-9999px;" href="http://americancensorship.org">STOP CENSORSHIP</a>';

    function isACD() {
        var start = new Date('Wed Nov 16 2011 00:00:01'),
            end = new Date('Thu Nov 17 2011 00:00:01'),
            now = new Date();
        return (start < now && now < end);
    }

    function isEnUS() {
        return document.location.pathname.indexOf('/en-US/') === 0;
    }

    function isLandingPage() {
        var view = document.location.pathname.slice(7);
        return _.indexOf(['home', 'mobile', 'sync', 'firefox-home'], view) >= 0;
    }

    function isInProduct() {
        return k.getReferrer(k.getQueryParamsAsDict()) === 'inproduct';
    }

    if (isACD() && isEnUS() && (isLandingPage() || isInProduct())) {
        $('#masthead').append(interpolate(html, [$('body').data('media-url')]));
    }

}(jQuery));