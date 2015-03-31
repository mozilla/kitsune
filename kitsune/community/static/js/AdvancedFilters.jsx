/* globals _:false, React:false */
import {Icon} from './contributors-common.jsx';
import cx from 'classnames';
import moment from 'moment';

const DATE_FORMAT = 'YYYY-MM-DD';

const availableFilters = {
    'last_contribution_date': {
        title: 'Days since last contribution',
        type: 'days_relative',
        ops: {
            /* Yes, these are backwards. It is beceause the real data type is
             * a date, but we are dealing with relative days.
             * "less than 3 days ago" translates to "date > (now - 3 days)"
             * The subtraction flips the comparotor.
             */
            'gt': 'less than',
            'lt': 'greater than',
        },
    },
};


/* This shows a button that counts the number of advanced filters in use, and
 * when clicked expands to show all of the filters.
 */
export default class AdvancedFilters extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            expanded: false,
        };
    }

    /** Expand or collapse the detail window. */
    toggleExpand() {
        var {expanded} = this.state;
        expanded = !expanded;
        this.setState({expanded});
    }

    /**
     * Get only the filters that are listed as "advanced filters" in
     * `availableFilters`. Filters with a name like "foo__op" are considered
     * equivalent to filters named "foo".
     */
    applicableFilters() {
        let applicableFilters = {};
        let availableFilterNames = [];
        _.forEach(availableFilters, (filter, name) => {
            _.forEach(filter.ops, (displayName, op) => {
                if (op === 'eq') {
                    availableFilterNames.push(name);
                } else {
                    availableFilterNames.push(`${name}__${op}`);
                }
            });
        });

        return _.pick(this.props.filters, ...availableFilterNames);
    }

    render() {
        return (
            <div className="AdvancedFilters">
                <AdvancedFiltersSummary
                    count={_.keys(this.applicableFilters()).length}
                    toggleExpand={this.toggleExpand.bind(this)}/>

                {this.state.expanded
                    ? <AdvancedFiltersDetails
                        filters={this.applicableFilters()}
                        setFilters={this.props.setFilters}
                        toggleExpand={this.toggleExpand.bind(this)}/>
                    : null}
            </div>
        )
    }
}

/* This shows the number of filters applied, and toggles expanding the window. */
class AdvancedFiltersSummary extends React.Component {
    render() {
        return (
            <div className="AdvancedFilters__summary Filters__item--button" onClick={this.props.toggleExpand}>
                <Icon name="filter"/>
                {this.props.count > 0
                    ? <span className="AdvancedFilters__summary__number">{this.props.count}</span>
                    : null}
            </div>
        );
    }
}

AdvancedFiltersSummary.propTypes = {
    count: React.PropTypes.number.isRequired,
    toggleExpand: React.PropTypes.func.isRequired,
};


let getFilterId = (function() {
    let next = 0;
    return function() {
        next++;
        return `filter-${next}`;
    }
})();


/* This shows a row for each filter. */
class AdvancedFiltersDetails extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            filters: this.convertFiltersIncoming(),
        };
    }

    /**
     * The filters passed to AdvancedFiltersDetails come in the form of a
     * mapping from names to values. This converts that into a list of objectss
     * like {name, op, value, id}. `op` comes from Django-style __ suffixes,
     * and `id` is just a simple global incrementing counter. This is used as
     * a React key when rendering filters.
     *
     * Example: {foo__gt: 5, bar: 4} would be serialized as [
     *   {name: foo, op: gt, value: 4, id: <ID>},
     *   {name: bar, op: eq, value: 5, id: <ID>},
     * ]
     *
     * @returns {Array} A list of filter objects.
     */
    convertFiltersIncoming(props=this.props) {
        return _.map(props.filters, (value, name) => {
            let op;
            if (name.indexOf('__') >= -1) {
                [, name, op] = /(.*)__(.*)/.exec(name);
            } else {
                op = 'eq';
            }
            return {name, op, value, id: getFilterId()};
        });
    }

    /**
     * The internal format of filters is a list of filter objects. This
     * converts those back into a map of filter names to filter values.
     *
     * @returns {Object} A map of filter names to filter values.
     */
    convertFiltersOutgoing() {
        let externalFilters = this.props.filters;
        let internalFilters = this.state.filters;
        var newFilters = {};
        // Clear all the old filters out. We can't reliable update them in place.
        _.forEach(externalFilters, (_, key) => {newFilters[key] = undefined; });
        // set all the new filters
        _.forEach(internalFilters, (filter) => {
            let fullName = filter.name;
            if (filter.op !== 'eq') {
                fullName += '__' + filter.op;
            }
            newFilters[fullName] = filter.value;
        });
        return newFilters;
    }

    componentWillReceiveProps(newProps) {
        this.setState({
            filters: this.convertFiltersIncoming(newProps),
        });
    }

    /**
     * Update the internal state of the detail view in response to a change event
     * usually on a form input. If the event did not come directly from a form
     * input, then an optional name and value can be passed.
     *
     * @param {Number} idx Index of the filter being updated.
     * @param {Event} ev Event that triggered this. Will be `preventDefault`ed.
     * @param {String} [name=ev.target.name] Name of the field to update. By default,
     *     this will be pulled from the target element's name attribute.
     * @param {String} [name=ev.target.value] Value of the field to update. By default,
     *     this will be pulled from the target element's value attribute.
     */
    handleChange(idx, ev, name=ev.target.name, value=ev.target.value) {
        ev.preventDefault();
        let {filters} = this.state;
        filters[idx][name] = value;
        this.setState({filters});
    }

    /**
     * Adds a new filter to the UI.
     *
     * Calls `ev.preventDefault`.
     *
     * @param {Event} ev The event that triggered this. Will be `preventDefault`ed.
     */
    addFilter(ev) {
        ev.preventDefault();
        let {filters} = this.state;
        /* TODO: This just hard codes a default in, but there should probably
         * be a way to have a null filter. */
        filters.push({
            name: 'last_contribution_date',
            op: 'gt',
            value: moment().subtract(7, 'days').format(DATE_FORMAT),
            id: getFilterId(),
        });
        this.setState({filters});
    }

    /**
     * Remove a filter, by index.
     *
     * @param {Number} idx The index of the filter to remove.
     * @param {Event} ev The event that triggered this action. Will be `preventDefault`ed.
     */
    removeFilter(idx, ev) {
        ev.preventDefault();
        let {filters} = this.state;
        filters.splice(idx, 1);
        this.setState({filters});
    }

    /**
     * Commit all internal state to external filters, and close the dialog.
     */
    commit() {
        this.props.setFilters(this.convertFiltersOutgoing());
        this.props.toggleExpand();
    }

    render() {
        return (
            <div className="Filters__window AdvancedFilters__detail">
                <h2>Filters</h2>
                <ul>
                    {this.state.filters.map((filter, idx) => (
                        <AdvancedFilterLine {...filter}
                            key={filter.id}
                            onChange={this.handleChange.bind(this, idx)}
                            remove={this.removeFilter.bind(this, idx)}/>
                    ))}
                    <li>
                        <a href="#" onClick={this.addFilter.bind(this)}>Add another filter</a>
                    </li>
                </ul>
                <div className="AdvancedFilters__detail__actions">
                    <button className="btn" onClick={this.props.toggleExpand}>Cancel</button>
                    <button className="btn btn-submit" onClick={this.commit.bind(this)}>
                        Apply
                    </button>
                </div>
            </div>
        );
    }
}

/** This is a single row in the filter view. */
class AdvancedFilterLine extends React.Component {
    render() {
        let valueInput;
        if (availableFilters[this.props.name].type === 'days_relative') {
            valueInput = <DayRelativeComponent
                name="value"
                value={this.props.value}
                onChange={this.props.onChange}/>;
        } else {
            valueInput = <input
                name="value"
                value={this.props.value}
                onChange={this.props.onChange}/>;
        }

        return <li className="AdvancedFilters__detail__filterRow">
            <select name="name" value={this.props.name} onChange={this.props.onChange}>
                {_.map(availableFilters, (filter, name) =>
                    <option key={filter} value={filter.name}>{filter.title}</option>
                )}
            </select>
            <select name="op" value={this.props.op} onChange={this.props.onChange}>
                {_.map(availableFilters[this.props.name].ops, (displayName, op) => (
                    <option key={op} value={op}>{displayName}</option>
                ))}
            </select>
            {valueInput}
            <a href="#" onClick={this.props.remove}>Remove</a>
        </li>;
    }
}

/**
 * The input for this is a date represented as a string. The value shown to the
 * user is the number of days ago that date was.
 */
class DayRelativeComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            daysAgo: moment().diff(moment(this.props.value), 'days'),
            valid: true,
        };
    }

    handleChange(ev) {
        this.setState({daysAgo: ev.target.value});
        let daysAgo = parseInt(ev.target.value);
        if (isNaN(daysAgo)) {
            this.setState({valid: false});
        } else {
            this.setState({valid: true});
            let targetDate = moment().subtract(daysAgo, 'days').format(DATE_FORMAT);
            this.props.onChange(ev, this.props.name, targetDate);
        }
    }

    render() {
        return <input
            valid
            name={this.props.name}
            value={this.state.daysAgo}
            onChange={this.handleChange.bind(this)}/>;
    }
}
