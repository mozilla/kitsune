var dataEl = document.querySelector('script[name="locale-data"]');
export const locales = JSON.parse(dataEl.innerHTML);

export class CommunityFilters extends React.Component {
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

            <select name="locale" defaultValue={this.props.filters.locale} onChange={this.handleChange.bind(this)}>
                <option value="">Select a locale</option>
                {
                    locales.map(([name, code]) => <option key={code} value={code}>{name}</option>)
                }
            </select>
        </div>;
    }
}

export class UserChip extends React.Component {
    render() {
        return (
            <span className="user-chip" title={this.props.username}>
                <img src={this.props.avatar}/>
                {this.props.display_name || this.props.username}
            </span>
        );
    }
}

export class RelativeTime extends React.Component {
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

export class Icon extends React.Component {
    render() {
        return <i className={'fa fa-' + this.props.name}/>;
    }
}

export class Paginator extends React.Component {
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
