import Result from './Result.jsx';

export default class SearchResults extends React.Component {
    render() {
        var results = this.props.data.map(function (result) {
            return (
                <Result
                    title={result.title}
                    content={result.content}
                    type="question" />
            );
        });

        return (
            <section id="search-results">
                <div className="content-box">
                    {results}
                </div>
            </section>
        );
    }
}
