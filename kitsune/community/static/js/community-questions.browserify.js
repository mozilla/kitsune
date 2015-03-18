/* jshint esnext: true */
/* globals React:false */
import QuestionsContributors from './QuestionsContributors.jsx';
import CommunityController from './CommunityController.js';

window.onpopstate = function() {
    refresh();
}

var controller = new CommunityController('questions', QuestionsContributors, document.querySelector('#main-content'));
controller.render();
