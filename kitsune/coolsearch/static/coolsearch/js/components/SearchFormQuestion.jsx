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
    this.updateQueryFunction = QueryActionCreator.updateQueryQuestion;
  }
}
