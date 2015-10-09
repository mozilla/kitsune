/*
React component that controls the knowledge base specific part of the
Search form.
Shows the inputs to search the "wiki" documents.
*/

import Select from 'react-select';

import QueryActionCreator from '../actions/QueryActionCreator.js';
import SearchFormBase from './SearchFormBase.jsx';


export default class SearchFormWiki extends SearchFormBase {
  constructor(props) {
    super(props);

    this.itemName = 'Article';
    this.updateFiltersFunction = QueryActionCreator.updateFiltersWiki;

    this.filters = [
      'language',
      'category',
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
