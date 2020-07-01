/* globals k:false, _:false, React:true, $:false */
import ContributorsList from "./ContributorsList.jsx";

export default class ContributorsController {
  constructor({ area, target, title, columns }) {
    this.area = area;
    this.columns = columns;
    this.target = target;
    this.title = title;

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
    history.pushState(null, "", qs);
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
        this.target.textContent =
          "Something went wrong! " + JSON.stringify(err);
      });
  }

  render() {
    React.render(
      <ContributorsList
        data={this.data}
        setFilters={this.setFilters.bind(this)}
        title={this.title}
        columns={this.columns}
      />,
      this.target
    );
  }
}
