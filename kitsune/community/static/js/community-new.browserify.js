/* jshint esnext: true */
/* globals React:false */
import {CommunityResults} from './TopContributors.jsx';

class TopContributors {
    constructor(targetEl) {
        this.targetEl = targetEl;
        this.filters = k.getQueryParamsAsDict() || {};
        var dataEl = document.querySelector('script[name="contributor-data"]');
        this.data = JSON.parse(dataEl.innerHTML);
    }

    setFilters(newFilters) {
        var allSame = true;
        _.forEach(newFilters, (value, key) => {
            if (this.filters[key] !== value) {
                allSame = false;
            }
        });

        if (allSame) {
            return;
        }

        _.extend(this.filters, newFilters);
        var qs = k.queryParamStringFromDict(this.filters);
        history.pushState(null, '', qs);
        this.refresh();
    }

    refresh() {
        var qs = window.location.search;
        var url = '/api/2/topcontributors/questions/' + qs;
        $.getJSON(url)
        .done((data) => {
            this.data = data;
            this.render();
        })
        .fail(function(err) {
            this.targetEl.textContent = 'Something went wrong! ' + JSON.stringify(err);
        });
    }

    render() {
        var el = <CommunityResults
            data={this.data}
            setFilters={this.setFilters.bind(this)}/>;
        React.render(el, this.targetEl);
    }
}

window.onpopstate = function() {
    refresh();
}

var controller = new TopContributors(document.querySelector('#main-content'));
controller.render();
