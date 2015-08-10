/* globals Marky:false, jQuery:false */
/*
 * JS for Groups app
 */

(function($) {

  'use strict';

  function init() {
    // Marky for information edit:
    var buttons = Marky.allButtons();
    Marky.createCustomToolbar('.editor-tools', '#id_information', buttons);
  }

  $(document).ready(init);

})(jQuery);
