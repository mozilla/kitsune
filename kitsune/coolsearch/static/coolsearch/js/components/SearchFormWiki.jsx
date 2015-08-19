/*
React component that controls the knowledge base specific part of the
Search form.
Shows the inputs to search the "wiki" documents.
*/

import QueryActionCreator from '../actions/QueryActionCreator.js';
import SearchFormBase from './SearchFormBase.jsx';


export default class SearchFormForum extends SearchFormBase {
  constructor(props) {
    super(props);

    this.itemName = 'Article';
    this.updateQueryFunction = QueryActionCreator.updateQueryWiki;
  }
}
