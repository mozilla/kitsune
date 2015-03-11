(function() {

    var CommunityResults = k.react.CommunityResults;
    var mainContentEl = document.querySelector('#main-content');
    var data;
    var filters = k.getQueryParamsAsDict() || {};

    function firstLoad() {
        var dataEl = document.querySelector('script[name="contributor-data"]')
        data = JSON.parse(dataEl.innerHTML);
        render();
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

    function render() {
        var el = <CommunityResults
            data={data}
            filters={filters}
            setFilters={setFilters}/>
        React.render(el, mainContentEl);
    }

    function refresh() {
        var qs = window.location.search;
        var url = '/api/2/topcontributors/questions/' + qs;
        $.getJSON(url)
        .done(function(_data) {
            data = _data;
            render();
        })
        .fail(function(err) {
            mainContenEl.textContent = 'Something went wrong! ' + JSON.stringify(err);
        });
    }

    firstLoad();
})();
