/*
React component that controls the questions specific part of the
Search form.
Shows the inputs to search the "question" documents.
*/

import QueryActionCreator from '../actions/QueryActionCreator.js';


export default class SearchFormQuestion extends React.Component {
  updateQuery(event) {
    var query = {
      query: event.target.value.trim(),
    };

    QueryActionCreator.updateQueryQuestion(query);
  }

  render() {
    return (
      <div>
        <fieldset className="query">
          <span>Post contains: </span>
          <input
            type="text"
            placeholder="crashes on youtube"
            onChange={this.updateQuery.bind(this)} />
        </fieldset>
      </div>
    );
  }
}
