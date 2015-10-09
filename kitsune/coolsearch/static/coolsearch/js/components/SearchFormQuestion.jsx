/*
React component that controls the questions specific part of the
Search form.
Shows the inputs to search the "question" documents.
*/

import QueryActionCreator from '../actions/QueryActionCreator.js';
import SearchFormBase from './SearchFormBase.jsx';


export default class SearchFormQuestion extends SearchFormBase {
  constructor(props) {
    super(props);

    this.itemName = 'Post';
    this.updateFiltersFunction = QueryActionCreator.updateFiltersQuestion;

    this.filters = [
      'product',
      'topics',
    ];
  }

  _updateSelectFilter(filterName) {
    return (valStr, valArr) => {
      var values = valArr.map(elem => elem.value);
      this._updateFilter(filterName, values);
    }
  }

  render() {
    var fieldsets = this.filters.map(item => {
      var filter = this.props.parameters[item];
      return (
        <fieldset>
          <span>{filter.meta.label}</span>
          <Select
            name={filter.meta.name}
            value={this.props.filters[filter.meta.name]}
            options={filter.options}
            multi={filter.meta.multi}
            onChange={this._updateSelectFilter(filter.meta.name)}
          />
        </fieldset>
      );
    });

    return this._render(
      <div>
        {fieldsets}
      </div>
    );
  }
}
