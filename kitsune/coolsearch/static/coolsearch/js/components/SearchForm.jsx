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


export default class SearchForm extends React.Component {
  constructor(props) {
    super(props);

    this.state = this._getStateFromStores();

    this.startQuery = _.debounce(this.getResults.bind(this), 300);
  }

  _getStateFromStores () {
    return {
      query: QueryStore.getCurrentQuery(),
      currentForm: QueryStore.getCurrentForm()
    };
  }

  componentDidMount() {
    QueryStore.addChangeListener(this._onChange.bind(this));
  }

  _onChange() {
    this.setState(this._getStateFromStores());
    this.startQuery();
  }

  getResults(e) {
    if (e) {
      e.preventDefault();
    }

    SearchActionCreator.runSearch(this.state.currentForm, this.state.query);
  }

  handleSelect(index) {
    var tabsOrder = ['wiki', 'question', 'forum'];
    var currentForm = tabsOrder[index];
    QueryActionCreator.updateCurrentForm(currentForm);
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
      </form>
    );
  }
}
