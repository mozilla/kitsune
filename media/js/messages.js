/*
 * Make textarea in replies auto expanding.
 * Private messaging.
 */

$(document).ready(function(){
    // Hide reply button and shrink the textarea
    var $area = $('#read-message textarea#id_message');
    $area.attr('placeholder', gettext('Reply...'));
    $('#read-message .editor-tools').hide();
    $('#read-message input[type=submit]').hide();

    // Show the orginal button and expanding extarea
    $area.one('focus',function(){
        $area.autoResize();
        $('#read-message .editor-tools').show();
        $('#read-message input[type=submit]').show();
        Marky.createSimpleToolbar('.editor-tools', '#id_message');
        new k.AjaxPreview($('#preview-btn'), {
            changeHash: false
        });
    })
});
