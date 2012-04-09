/*
 * home.js
 * Scripts for the landing pages.
 */

(function ($) {
    function init() {
        $('img.lazy').lazyload();
        ShowFor.initForTags();
        initClearOddSections();
    }

    // Add `odd` CSS class to home page content sections for older browsers.
    function initClearOddSections() {
        clearOddSections();
        $('#os, #browser').change(clearOddSections);
    }

    function clearOddSections() {
        var odd = true;
        $('#home-content-explore section').removeClass('odd');
        $('#home-content-explore section:visible').each(function(){
            // I can't use :nth-child(odd) because of showfor
            if (odd) {
                $(this).addClass('odd');
            }
            odd = !odd;
        });
    }

    $(document).ready(init);

}(jQuery));

