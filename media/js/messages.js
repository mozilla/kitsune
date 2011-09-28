/*
 * Private messaging.
 */

(function($){

    function init() {
        Marky.createSimpleToolbar('.editor-tools', '#id_message');
        new k.AjaxPreview($('#preview-btn'), {
            changeHash: false
        });
    }

    $(document).ready(init);

}(jQuery));
