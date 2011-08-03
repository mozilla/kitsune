(function() {
    $(document).ready(function() {
        var s = new io.Socket(window.location.hostname, {
          port: 3000,
          rememberTransport: false,
          // 'websocket' disabled because FF7 throws AttributeErrors on connect:
          transports: ['xhr-multipart', 'xhr-polling'],
          resource: 'socket.io'
        });
        s.connect();

        s.addEvent('connect', function() {
            var nonce = $('#chatform input[name=nonce]').val();
            if (nonce.length)
                s.send(JSON.stringify({'kind': 'nonce', 'nonce': nonce}));
            s.send(JSON.stringify({'kind': 'join', 'room': 'world'}));
        });

        s.addEvent('message', function(data) {
            var $chatbox, template;
            data = JSON.parse(data);
            // TODO: Pay attention to room when picking $chatbox.
            $chatbox = $('#chatbox');
            switch (data['kind']) {
                case 'say':
                    template = gettext('<div class="say"><span class="user">%(user)s</span>%(message)s</div>');
                    break;
                case 'join':
                    template = gettext('<div class="join"><span class="user">%(user)s</span> joined the chat.</div>');
                    // TODO: Update the display of users in the chat.
                    break;
                case 'leave':
                    template = gettext('<div class="join"><span class="user">%(user)s</span> left the chat.</div>');
                    // TODO: Update the display of users in the chat.
                    break;
            }
            $chatbox.append(interpolate(template, data, true))
                    .scrollTop($chatbox[0].scrollHeight);
        });

        // Send the message when submit is clicked:
        $('#chatform').submit(function(evt) {
            var line = $('#chatform [type=text]').val();
            if (line !== '') {
                $('#chatform [type=text]').val('');
                s.send(JSON.stringify({'kind': 'say', 'room': 'world', 'message': line}));
            }
            $(this).trigger('ajaxComplete');
            return false;
        });
    });
})();
