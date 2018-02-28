(function(Mozilla) {
  'use strict';

  // callback for UITour conditional
  var rogerThat = function(sync) {

    // only run if not syncing
    var notSyncing = !sync.detail.data.setup;

    if (notSyncing) {

      var showPromotion = function(variation) {
        document.addEventListener('DOMContentLoaded', function() {
          var promotions = document.getElementById('promotions');
          var showSpan = promotions.querySelector('span[data-variation="'+variation+'"]');
          var links = promotions.getElementsByTagName('a');

          for (var i=0; i<links.length; i++) {
            links[i].href = links[i].href + '&utm_term=' + variation;
          }

          showSpan.className = showSpan.className.replace('hidden', '');
          promotions.className = promotions.className.replace('hidden', '');
        });
      };

      var laverneHooks = new Mozilla.TrafficCop({
        id: 'experiment-fxa-cta-topbar',
        customCallback: showPromotion,
        variations: {
          'a': 25,
          'b': 25,
          'c': 25,
          'd': 25
        }
      });

      laverneHooks.init();
    }
  };

  // only run on Firefox
  var isFirefox = /\sFirefox/.test(navigator.userAgent);

  if (isFirefox) {
    var event = new CustomEvent('mozUITour', {
      bubbles: true,
      detail: {
        action: 'getConfiguration',
        data: {configuration: 'sync'}
      }
    });

    document.addEventListener('mozUITourResponse', rogerThat, {once: true});
    document.dispatchEvent(event);
  }

})(window.Mozilla);
