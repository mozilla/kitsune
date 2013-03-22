(function() {

function init() {
  $('input[type=date]').datepicker({
    dateFormat: 'yy-mm-dd'
  });

  $topics = $('#topic-stats');
  k.rickshaw.makeGraph($topics, $topics.data('histogram'));
}

$(document).ready(init);

})();
