/* jshint esnext: true */

import SearchController from './SearchController.jsx';

var controller = new SearchController({
    title: 'Advanced Search',
    target: document.getElementById('advanced-search')
});

controller.render();
