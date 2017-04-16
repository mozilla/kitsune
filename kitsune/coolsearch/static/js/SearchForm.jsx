export default class SearchForm extends React.Component {
    getResults(e) {
        e.preventDefault();

        var query = React.findDOMNode(this.refs.query).value.trim();

        // Now do something with that query...
    }

    render() {
        return (
            <form method="get" action="" onSubmit={this.getResults.bind(this)}>
                <fieldset>
                    <span>Contains: </span>
                    <input type="text" ref="query" placeholder="crashes on youtube" />
                </fieldset>
                <fieldset>
                    <button type="submit">Search Mozilla Support</button>
                </fieldset>
            </form>
        );
    }
}
