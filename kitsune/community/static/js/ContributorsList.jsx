/* globals React:false */
import {Paginator} from './contributors-common.jsx';
import CommunityFilters from './CommunityFilters.jsx';
import SelectTable from './SelectTable.jsx';

export default class ContributorsList extends React.Component {
    sendMessage(data) {
        var usernames = data.map((contributor) => contributor.user.username);
        window.location = `/messages/new?to=${usernames.join(',')}`;
    }

    render() {
        var filters = this.props.data.filters;
        var results = this.props.data.results;
        var fullCount = this.props.data.count;
        var allowedOrderings = this.props.data.allowed_orderings;

        var setFilters = this.props.setFilters;
        var pageSize = 10;
        var pageCount = Math.ceil(fullCount / pageSize);

        return <article className="community-results">
            <h1>{this.props.title}</h1>
            <CommunityFilters filters={filters} setFilters={setFilters}/>
            <SelectTable
                data={results}
                columns={this.props.columns}
                filters={filters}
                setFilters={setFilters}
                allowedOrderings={allowedOrderings}
                actions={[
                    {icon: 'paper-plane', onClick: this.sendMessage.bind(this), hover: 'Send PM'},
                ]}/>
            <Paginator filters={filters} setFilters={setFilters} pageCount={pageCount} />
        </article>;
    }
}
