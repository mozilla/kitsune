/*
React component that controls the behavior of the Search form.
Handles the tabs of the form and the triggering of search queries.
*/

import SwipeViews from 'react-swipe-views';

import SearchFormWiki from './SearchFormWiki.jsx';
import SearchFormQuestion from './SearchFormQuestion.jsx';
import SearchFormForum from './SearchFormForum.jsx';

import QueryStore from '../stores/QueryStore.js';

import QueryActionCreator from '../actions/QueryActionCreator.js';
import SearchActionCreator from '../actions/SearchActionCreator.js';


var getStateFromStores = function () {
  return {
    query: QueryStore.getCurrentQuery()
  };
};


export default class SearchForm extends React.Component {
  constructor(props) {
    super(props);

    this.state = getStateFromStores();
    this.currentForm = 'wiki';

    this.startQuery = _.debounce(this.startQuery.bind(this), 300);
  }

  componentDidMount() {
    QueryStore.addChangeListener(this._onChange.bind(this));
  }

  _onChange() {
    this.setState(getStateFromStores());
    this.startQuery();
  }

  getResults(e) {
    if (e) {
      e.preventDefault();
    }

    SearchActionCreator.runSearch(this.currentForm, this.state.query);
  }

  /** A debounced proxy to getResults(). */
  startQuery() {
    this.getResults();
  }

  handleSelect(index) {
    var tabsOrder = ['wiki', 'question', 'forum'];
    this.currentForm = tabsOrder[index];
    QueryActionCreator.updateCurrentForm(this.currentForm);
  }

  render() {
    return (
      <form method="get" action="" onSubmit={this.getResults.bind(this)}>
        <SwipeViews onIndexChange={this.handleSelect.bind(this)}>
          <div title="Knowledge Base">
            <SearchFormWiki query={this.state.query}/>
          </div>
          <div title="Support Questions">
            <SearchFormQuestion query={this.state.query}/>
          </div>
          <div title="Discussion Forums">
            <SearchFormForum query={this.state.query}/>
          </div>
        </SwipeViews>

        <fieldset className="controls">
          <button className="btn btn-important big" type="submit">
            Search Mozilla Support
          </button>
        </fieldset>
      </form>
    );
  }
}
