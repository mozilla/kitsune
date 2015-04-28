/*
React component that controls the forum specific part of the
Search form.
Shows the inputs to search the "forum" documents.
*/

import QueryActionCreator from '../actions/QueryActionCreator.js';


export default class SearchFormForum extends React.Component {
  updateQuery(event) {
    var query = {
      query: event.target.value.trim(),
    };

    QueryActionCreator.updateQueryForum(query);
  }

  render() {
    return (
      <div>
        <fieldset className="query">
          <span>Thread contains: </span>
          <input
            type="text"
            placeholder="crashes on youtube"
            onChange={this.updateQuery.bind(this)} />
        </fieldset>
      </div>
    );
  }
}
