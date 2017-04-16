/* jshint esnext: true */
import SearchForm from './SearchForm.jsx';
import SearchResults from './SearchResults.jsx';

export default class SearchController {
    constructor({target, title}) {
        this.target = target;
        this.title = title;
    }

    render() {
        React.render(
            <div>
                <h1 className="nomargin"
                    title="It's like Advanced Search, but cooler">Cool Search</h1>
                <SearchForm />
                <SearchResults
                    data={[{title: "Hello", content: "World"}]} />
            </div>,
            this.target
        );
    }
}
