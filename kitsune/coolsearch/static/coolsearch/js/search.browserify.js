/* jshint esnext: true */

import SearchController from './components/SearchController.jsx';

var controller = new SearchController({
    title: 'Advanced Search',
    target: document.getElementById('advanced-search')
});

controller.render();
