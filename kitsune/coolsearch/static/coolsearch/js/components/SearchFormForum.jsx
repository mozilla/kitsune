/*
React component that controls the forum specific part of the
Search form.
Shows the inputs to search the "forum" documents.
*/

import QueryActionCreator from '../actions/QueryActionCreator.js';
import SearchFormBase from './SearchFormBase.jsx';


export default class SearchFormForum extends SearchFormBase {
  constructor(props) {
    super(props);

    this.itemName = 'Thread';
    this.updateFiltersFunction = QueryActionCreator.updateFiltersForum;
  }

  render() {
    return this._render(
      <fieldset>
      </fieldset>
    );
  }
}
