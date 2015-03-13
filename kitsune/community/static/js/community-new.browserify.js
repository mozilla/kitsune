/* jshint esnext: true */
/* globals React:false */
import {CommunityResults} from './TopContributors.jsx';

var mainContentEl = document.querySelector('#main-content');
var filters = k.getQueryParamsAsDict() || {};

function firstLoad() {
    var dataEl = document.querySelector('script[name="contributor-data"]');
    var data = JSON.parse(dataEl.innerHTML);
    render(data);
}

function setFilters(newFilters) {
    var allSame = true;
    _.map(newFilters, function(value, key) {
        if (filters[key] !== value) {
            allSame = false;
        }
    });

    if (allSame) {
        return;
    }

    _.extend(filters, newFilters);
    var qs = k.queryParamStringFromDict(filters);
    history.replaceState(null, '', qs);
    refresh();
}

window.setFilters = setFilters;

function render(data) {
    var el = <CommunityResults
        data={data}
        setFilters={setFilters}/>;
    React.render(el, mainContentEl);
}

function refresh() {
    var qs = window.location.search;
    var url = '/api/2/topcontributors/questions/' + qs;
    $.getJSON(url)
    .done(render)
    .fail(function(err) {
        mainContentEl.textContent = 'Something went wrong! ' + JSON.stringify(err);
    });
}

firstLoad();
