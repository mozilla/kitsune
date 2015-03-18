/* jshint esnext: true */
/* globals React:false */
import L10nContributors from './L10nContributors.jsx';
import CommunityController from './CommunityController.js';

window.onpopstate = function() {
    refresh();
}

var controller = new CommunityController('l10n', L10nContributors, document.querySelector('#main-content'));
controller.render();
