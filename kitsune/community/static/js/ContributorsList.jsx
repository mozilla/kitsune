import {CommunityFilters, Paginator} from './contributors-common.jsx';
import SelectTable from './SelectTable.jsx';

export default class ContributorsList extends React.Component {
    render() {
        var filters = this.props.data.filters;
        var results = this.props.data.results;
        var fullCount = this.props.data.count;

        var setFilters = this.props.setFilters;
        var pageCount = Math.ceil(fullCount / Math.max(results.length, 1));

        return <article className="community-results">
            <h1>{this.props.title}</h1>
            <CommunityFilters filters={filters} setFilters={setFilters}/>
            <SelectTable contributors={results} columns={this.props.columns}/>
            <Paginator filters={filters} setFilters={setFilters} pageCount={pageCount} />
        </article>;
    }
}
