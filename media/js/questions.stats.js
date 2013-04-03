(function() {

function init() {
  $('input[type=date]').datepicker({
    dateFormat: 'yy-mm-dd'
  });

  $topics = $('#topic-stats');
  new k.Graph($topics, {
    data: {
      series: $topics.data('histogram')
    },
    options: {
      slider: false
    }
  }).render();
}

$(document).ready(init);

})();
