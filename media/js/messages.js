/*
 * Make textarea in replies auto expanding.
 * Private messaging.
 */

$(document).ready(function(){
    // Show the ajax preview on the new message page.
    Marky.createSimpleToolbar('#new-message .editor-tools', '#id_message');
    new k.AjaxPreview($('#preview-btn'), {
        changeHash: false
    });

    // Hide reply button and shrink the textarea.
    var $area = $('#read-message textarea#id_message');
    $area.attr('placeholder', gettext('Reply...'));
    $('#read-message .editor-tools').hide();
    $('#read-message input[type=submit]').hide();

    // Show the orginal button and expanding textarea.
    $area.one('focus',function(){
        $area.autoResize();
        $('#read-message .editor-tools').show();
        $('#read-message input[type=submit]').show();
        Marky.createSimpleToolbar('#read-message .editor-tools', '#id_message');
        new k.AjaxPreview($('#preview-btn'), {
            changeHash: false
        });
    });
});
