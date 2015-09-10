/*
React component that controls the forum specific part of the
Search form.
Shows the inputs to search the "forum" documents.
*/

import QueryStore from '../stores/QueryStore.js';

import QueryActionCreator from '../actions/QueryActionCreator.js';


export default class SearchFormBase extends React.Component {
  _updateFilter(name, value) {
    var filters = {};
    filters[name] = value;
    this.updateFiltersFunction(filters);
  }

  _updateQuery(event) {
    this._updateFilter('query', event.target.value.trim())
  }

  _render(content) {
    return (
      <div>
        <fieldset className="query">
          <span>{this.itemName} contains </span>
          <input
            type="text"
            placeholder="crashes on youtube"
            value={this.props.query}
            onChange={this._updateQuery.bind(this)} />
        </fieldset>
        {content}
      </div>
    );
  }
}
