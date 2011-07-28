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
            s.send(JSON.stringify({'kind': 'join', 'room': 'world'}));
        });

        s.addEvent('message', function(data) {
            var $chatbox;
            data = JSON.parse(data);
            if (data['kind'] == 'say') {
                $chatbox = $('#chatbox');
                // TODO: Pay attention to room.
                $chatbox.append('<div>' + data['message'] + '</div>').scrollTop($chatbox[0].scrollHeight);
            }
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
