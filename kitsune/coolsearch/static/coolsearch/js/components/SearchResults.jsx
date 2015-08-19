import SearchResult from './SearchResult.jsx';
import ResultsStore from '../stores/ResultsStore.js';


export default class SearchResults extends React.Component {
  constructor(props) {
    super(props);
    this.state = this._getStateFromStores();
    this.state.started = false;
  }

  componentDidMount() {
    ResultsStore.addChangeListener(this._onChange.bind(this));
  }

  _getStateFromStores () {
    return {
      results: ResultsStore.getAll(),
      count: ResultsStore.getCount()
    };
  }

  _onChange() {
    this.state.started = true;
    this.setState(this._getStateFromStores());
  }

  render() {
    var results = this.state.results.map(
      result => <SearchResult key={result.title} data={result} />
    );

    var resultsCountText = 'Run a search to get some results.';
    if (this.state.started) {
      if (this.state.count == 1) {
        resultsCountText = this.state.count + ' result found';
      }
      else {
        resultsCountText = this.state.count + ' results found';
      }
    }

    return (
      <section id="search-results">
        <div className="content-box">
          <div>
            {resultsCountText}
          </div>
          {results}
        </div>
      </section>
    );
  }
}
