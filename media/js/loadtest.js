/**
 * JavaScript load tests.
 *
 * Tests _must_ be behind some tunable flag or switch.
 */
(function() {
    /**
     * Hit the usernames autocomplete API with a random request
     * every few seconds. This is tuned with the
     * 'usernames-test' sample in Waffle.
     */
    function loadTestUsernamesAPI() {
        if (waffle.sample("usernames-test")) {
            var chars = "abcdefghijklmnopqrstuvwxyz",
                ival, i = 0, MAX = 20;
            ival = setInterval(function() {
                if (i >= MAX) {
                    clearInterval(ival);
                    return;
                }
                i++;
                var a = Math.floor(Math.random() * chars.length),
                    b = Math.floor(Math.random() * chars.length),
                    prefix = chars.substring(a, a+1) + chars.substring(b, b+1);
                $.ajax(
                    $("body").data("usernames-api"),
                    {
                       cache: false,
                       data: {"u": prefix},
                       error: function() {
                           clearInterval(ival);
                       }
                    });
            }, 20000);
        }
    }
    $(document).ready(loadTestUsernamesAPI);
})();
