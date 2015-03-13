/* jshint esnext: true */
/* globals React:false */
export class CommunityResults extends React.Component {
    render() {
        var filters = this.props.data.filters;
        var results = this.props.data.results;
        var fullCount = this.props.data.count;

        var setfilters = this.props.setFilters;
        var pageCount = Math.ceil(fullCount / Math.max(results.length, 1));

        return <article className="community-results">
            <CommunityHeader/>
            <CommunityFilters filters={filters} setFilters={setFilters}/>
            <ContributorsTable contributors={results}/>
            <Paginator filters={filters} setFilters={setFilters} pageCount={pageCount} />
        </article>;
    }
}

class CommunityHeader extends React.Component {
    render() {
        return <div>
            <h1>Top Contributors - Support Forum</h1>
        </div>;
    }
}

class CommunityFilters extends React.Component {
    handleChange(ev) {
        // React does some goofy stuff with events, so using when
        // something like _.throttle, the event has already been destroyed
        // by the time the throttled handler runs. So here we do it by hand.
        var value = ev.target.value;
        var newFilters = {page: null};

        if (value === '') {
            newFilters[ev.target.name] = null;
        } else {
            newFilters[ev.target.name] = value;
        }

        clearTimeout(this._timer);
        this._timer = setTimeout(this.props.setFilters.bind(null, newFilters), 200);
    }

    makeInput(name) {
        return <input name={name}
            autoComplete="off"
            defaultValue={this.props.filters[name]}
            onChange={this.handleChange.bind(this)}/>
    }

    render() {
        return <div className="filters">
            {this.makeInput('username')}
            {this.makeInput('startdate')}
            {this.makeInput('enddate')}
        </div>;
    }
}

class ContributorsTable extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            selections: props.contributors.map(function() { return false; })
        }
    }

    handleSelection(index, value) {
        var selections = this.state.selections;
        selections[index] = value;
        this.setState({selections: selections});
    }

    handleSelectAll(value) {
        var selections = this.state.selections;
        selections = selections.map(function() { return value; });
        this.setState({selections: selections});
    }

    render() {
        if (this.props.contributors.length > 0) {
            return <div>
                <table className="top-contributors">
                    <ContributorsTableHeader
                        selections={this.state.selections}
                        onSelectAll={this.handleSelectAll.bind(this)}/>
                    <ContributorsTableBody
                        contributors={this.props.contributors}
                        selections={this.state.selections}
                        onSelect={this.handleSelection.bind(this)}/>
                </table>
            </div>;
        } else {
            return <h2>No contributors match filters.</h2>;
        }
    }
}

class ContributorsTableHeader extends React.Component {
    handleChange(e) {
        e.stopPropagation();
        this.props.onSelectAll(e.target.checked);
    }

    render() {
        function and(a, b) { return a && b; }
        var allSelected = this.props.selections.reduce(and, true);

        return (
            <thead>
                <tr className="top-contributors-header">
                    <th data-column="select">
                        <input type="checkbox" ref="selectAll"
                            checked={allSelected}
                            onChange={this.handleChange.bind(this)}/>
                    </th>
                    <th data-column="rank">Rank</th>
                    <th data-column="user">Name</th>
                    <th data-column="answer-count">Answers</th>
                    <th data-column="solution-count">Solutions</th>
                    <th data-column="helpful-vote-count">Helpful Votes</th>
                    <th data-column="last-activity">Last Activity</th>
                    <th data-column="actions"></th>
                </tr>
            </thead>
        );
    }
}

class ContributorsTableBody extends React.Component {
    render() {
        return (
            <tbody>
                {this.props.contributors.map(function(contributor, i) {
                    return <ContributorsTableRow
                        selected={this.props.selections[i]}
                        onSelect={(val) => this.props.onSelect(i, val)}
                        key={contributor.user.username}
                        {...contributor}/>;
                }.bind(this))}
            </tbody>
        );
    }
}

class ContributorsTableRow extends React.Component {
    handleChange(e) {
        e.stopPropagation();
        this.props.onSelect(e.target.checked);
    }

    render() {
        return (
            <tr className="top-contributors-row">
                <td data-column="select">
                    <input type="checkbox" checked={this.props.selected} onChange={this.handleChange.bind(this)}/>
                </td>
                <td data-column="rank">
                    {this.props.rank}
                </td>
                <td data-column="user">
                    <UserChip {...this.props.user}/>
                </td>
                <td data-column="answer-count">
                    {this.props.answer_count}
                </td>
                <td data-column="solution-count">
                    {this.props.solution_count}
                </td>
                <td data-column="helpful-vote-count">
                    {this.props.helpful_vote_count}
                </td>
                <td data-column="last-contribution-date">
                    <RelativeTime timestamp={this.props.last_contribution_date} future={false}/>
                </td>
                <td data-column="actions">
                    <Icon name="paper-plane"/>
                </td>
            </tr>
        );
    }
}

class UserChip extends React.Component {
    render() {
        return (
            <span className="user-chip" title={this.props.username}>
                <img src={this.props.avatar}/>
                {this.props.display_name || this.props.username}
            </span>
        );
    }
}

class RelativeTime extends React.Component {
    render() {
        var timestamp = moment(this.props.timestamp);
        if (!timestamp.isValid()) {
            return <span>Never</span>;
        }
        // Limit to the present or the past, not the future.
        if (!this.props.future && timestamp.isAfter(moment())) {
            timestamp = moment();
        }
        return <time dateTime={this.props.timestamp}>{timestamp.fromNow()}</time>;
    }
}
RelativeTime.defaultProps = { future: true };

class Icon extends React.Component {
    render() {
        return <i className={'fa fa-' + this.props.name}/>;
    }
}

class Paginator extends React.Component {
    changePage(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this.props.setFilters({page: ev.target.dataset.page});
    }

    makeSelector(page, {text=null, selected=false}={}) {
        return <PaginatorSelector
                filters={this.props.filters}
                changePage={this.changePage.bind(this)}
                page={page}
                text={text}
                key={`page-${text || page}`}
                selected={selected}/>
    }

    render() {
        var currentPage = parseInt(this.props.filters.page);
        if (isNaN(currentPage)) {
            currentPage = 1;
        }
        var pageCount = this.props.pageCount;
        var firstPage = Math.max(1, currentPage - 4);
        var lastPage = Math.min(currentPage + 5, pageCount);
        var pageSelectors = [];

        // Previous button
        if (currentPage > 1) {
            pageSelectors.push(this.makeSelector(currentPage - 1, {text: 'Previous'}));
        }

        // First page button
        if (firstPage >= 2) {
            pageSelectors.push(this.makeSelector(1));
        }
        if (firstPage >= 3) {
            pageSelectors.push(<li key="skip" className="skip">…</li>);
        }

        // Normal buttons
        for (var i = firstPage; i <= lastPage; i++) {
            pageSelectors.push(this.makeSelector(i, {selected: i === currentPage}));
        }

        // Next button
        if (currentPage < pageCount) {
            pageSelectors.push(this.makeSelector(currentPage + 1, {text: 'Next'}));
        }

        return <ol className="pagination">{pageSelectors}</ol>;
    }
}

class PaginatorSelector extends React.Component {
    render() {
        var page = this.props.page;
        var pageFilters = _.extend({}, this.props.filters, {page: page});
        var pageUrl = k.queryParamStringFromDict(pageFilters);
        var liClasses = [];
        var aClasses = [];

        if (this.props.selected) {
            liClasses.push('selected');
            aClasses.push('btn-page');
        }
        if (this.props.text) {
            var textSlug = this.props.text.toLowerCase();
            liClasses.push(textSlug);
            aClasses.push('btn-page');
            aClasses.push('btn-page-' + textSlug);
        }

        return (
            <li className={liClasses.join(' ')}>
                <a href={pageUrl} className={aClasses.join(' ')} data-page={page} onClick={this.props.changePage}>
                    {this.props.text || this.props.page}
                </a>
            </li>
        );
    }
}

PaginatorSelector.defaultProps = {
    page: 1,
    text: null,
    selected: false,
};
