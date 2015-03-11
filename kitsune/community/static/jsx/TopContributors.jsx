(function() {
    var CommunityResults = React.createClass({
        render: function() {
            var filters = this.props.filters;
            var setfilters = this.props.setFilters;
            var results = this.props.data.results;
            var fullCount = this.props.data.count;
            var pageCount = Math.ceil(fullCount / Math.max(results.length, 1));

            return <article className="community-results">
                <CommunityHeader/>
                <CommunityFilters filters={filters} setFilters={setFilters}/>
                <ContributorsTable contributors={results}/>
                <Paginator filters={filters} setFilters={setFilters} pageCount={pageCount} />
            </article>
        }
    });

    var CommunityHeader = React.createClass({
        render: function() {
            return <div>
                <h1>Top Contributors - Support Forum</h1>
                <h2>Last 90 days</h2>
            </div>;
        },
    });

    var CommunityFilters = React.createClass({
        handleChange: function(ev) {
            // React does some goofy stuff with events, so using when
            // something like _.throttle, the event has already been destroyed
            // by the time the throttled handler runs. So here we do it by hand
            // with loads of binding and parameter passing. :(
            var value = ev.target.value;
            var newFilters = {page: null};

            if (value === '') {
                newFilters[ev.target.name] = null;
            } else {
                newFilters[ev.target.name] = value;
            }

            clearTimeout(this._timer);
            this._timer = setTimeout(this.props.setFilters.bind(null, newFilters), 200);
        },

        render: function() {
            return <div className="filters">
                <input name="username"
                    autoComplete="off"
                    defaultValue={this.props.filters.username}
                    onChange={this.handleChange}/>
            </div>;
        }
    });

    var ContributorsTable = React.createClass({
        getInitialState: function() {
            return {
                selections: this.props.contributors.map(function() { return false; })
            };
        },

        handleSelection: function(index, value) {
            var selections = this.state.selections;
            selections[index] = value;
            this.setState({selections: selections});
        },

        handleSelectAll: function(value) {
            var selections = this.state.selections;
            selections = selections.map(function() { return value; })
            this.setState({selections: selections});
        },

        render: function() {
            if (this.props.contributors.length > 0) {
                return <div>
                    <table className="top-contributors">
                        <ContributorsTableHeader
                            selections={this.state.selections}
                            onSelectAll={this.handleSelectAll}/>
                        <ContributorsTableBody
                            contributors={this.props.contributors}
                            selections={this.state.selections}
                            onSelect={this.handleSelection}/>
                    </table>
                </div>
            } else {
                return <h2>No contributors match filters.</h2>;
            }
        }
    });

    var ContributorsTableHeader = React.createClass({
        handleChange: function(e) {
            e.stopPropagation();
            this.props.onSelectAll(e.target.checked);
        },

        render: function() {
            function and(a, b) { return a && b }
            var allSelected = this.props.selections.reduce(and, true);

            return (
                <thead>
                    <tr className="top-contributors-header">
                        <th data-column="select">
                            <input type="checkbox" ref="selectAll"
                                checked={allSelected}
                                onChange={this.handleChange}/>
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
    });

    var ContributorsTableBody = React.createClass({
        render: function() {
            return (
                <tbody>
                    {this.props.contributors.map(function(contributor, i) {
                        return <ContributorsTableRow
                            selected={this.props.selections[i]}
                            onSelection={this.props.onSelect.bind(null, i)}
                            key={contributor.user.username}
                            {...contributor}/>
                    }.bind(this))}
                </tbody>
            );
        }
    });

    var ContributorsTableRow = React.createClass({
        handleChange: function(e) {
            e.stopPropagation();
            this.props.onSelection(e.target.checked);
        },

        render: function() {
            return (
                <tr className="top-contributors-row">
                    <td data-column="select">
                        <input type="checkbox" checked={this.props.selected} onChange={this.handleChange}/>
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
    });

    var UserChip = React.createClass({
        render: function() {
            return (
                <span className="user-chip" title={this.props.username}>
                    <img src={this.props.avatar}/>
                    {this.props.display_name || this.props.username}
                </span>
            );
        }
    });

    var RelativeTime = React.createClass({
        getDefaultProps: function() {
            return {
                future: true
            }
        },

        render: function() {
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
    });

    var Icon = React.createClass({
        render: function() {
            return <i className={'fa fa-' + this.props.name}/>;
        }
    });

    var Paginator = React.createClass({
        changePage: function(ev) {
            ev.preventDefault();
            ev.stopPropagation();
            this.props.setFilters({page: ev.target.dataset.page});
        },

        render: function() {
            var currentPage = parseInt(this.props.filters.page);
            if (isNaN(currentPage)) {
                currentPage = 1;
            }
            var pageCount = this.props.pageCount;
            var firstPage = Math.max(1, currentPage - 4);
            var lastPage = Math.min(currentPage + 5, pageCount);
            var pageSelectors = [];
            var pageFilters;
            var pageUrl;

            // Previous button
            if (currentPage > 1) {
                pageSelectors.push(<PaginatorSelector
                    filters={this.props.filters}
                    changePage={this.changePage}
                    page={currentPage - 1}
                    text="Previous"
                    key="page-previous"/>);
            }

            // First page button
            if (firstPage >= 2) {
                pageSelectors.push(<PaginatorSelector
                    filters={this.props.filters}
                    changePage={this.changePage}
                    key="page-1"/>);
            }
            if (firstPage >= 3) {
                pageSelectors.push(<li class="skip">…</li>);
            }

            // Normal buttons
            for (var i = firstPage; i <= lastPage; i++) {
                pageSelectors.push(<PaginatorSelector
                    filters={this.props.filters}
                    changePage={this.changePage}
                    page={i}
                    selected={i === currentPage}
                    key={"page-" + i} />);
            }

            // Next button
            if (currentPage < pageCount) {
                pageSelectors.push(<PaginatorSelector
                    filters={this.props.filters}
                    changePage={this.changePage}
                    page={currentPage + 1}
                    text="Next"
                    key="page-next"/>);
            }

            return <ol className="pagination">{pageSelectors}</ol>;
        }
    });

    var PaginatorSelector = React.createClass({
        getDefaultProps: function() {
            return {
                page: 1,
                text: null,
                selected: false
            }
        },

        render: function() {
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
    });


    var k = window.k || {};
    k.react = k.react || {};
    k.react.CommunityResults = CommunityResults;


})();
