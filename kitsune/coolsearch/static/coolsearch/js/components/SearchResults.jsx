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

    return (
      <section id="search-results">
        <div className="content-box">
          <div>
            {this.state.started ? this.state.count + ' results found' : 'Run a search to get some results.'}
          </div>
          {results}
        </div>
      </section>
    );
  }
}
