/*
React component that controls the knowledge base specific part of the
Search form.
Shows the inputs to search the "wiki" documents.
*/

import QueryActionCreator from '../actions/QueryActionCreator.js';


export default class SearchFormWiki extends React.Component {
  updateQuery(event) {
    var query = {
      query: event.target.value.trim(),
    };

    QueryActionCreator.updateQueryWiki(query);
  }

  render() {
    return (
      <div>
        <fieldset className="query">
          <span>Article contains: </span>
          <input
            type="text"
            placeholder="crashes on youtube"
            onChange={this.updateQuery.bind(this)} />
        </fieldset>
      </div>
    );
  }
}
