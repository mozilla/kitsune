import SearchResult from './SearchResult.jsx';
import ResultsStore from '../stores/ResultsStore.js';


var getStateFromStores = function () {
  return {
    results: ResultsStore.getAll(),
    count: ResultsStore.getCount()
  };
};

export default class SearchResults extends React.Component {
  constructor(props) {
    super(props);
    this.state = getStateFromStores();
    this.state.started = false;
  }

  componentDidMount() {
    ResultsStore.addChangeListener(this._onChange.bind(this));
  }

  _onChange() {
    this.state.started = true;
    this.setState(getStateFromStores());
  }

  render() {
    var results = this.state.results.map(function (result) {
      return (
        <SearchResult
          key={result.title}
          data={result}
        />
      );
    });

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
