export default class ContributorsController {
    constructor(area, Component, targetEl) {
        this.area = area;
        this.Component = Component;
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
        var url = `/api/2/topcontributors/${this.area}/${qs}`;
        $.getJSON(url)
        .done((data) => {
            this.data = data;
            this.render();
        })
        .fail((err) => {
            this.targetEl.textContent = 'Something went wrong! ' + JSON.stringify(err);
        });
    }

    render() {
        React.render(
            <this.Component data={this.data} setFilters={this.setFilters.bind(this)}/>,
            this.targetEl);
    }
}
