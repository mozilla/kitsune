import {Icon} from './contributors-common.jsx';
import cx from 'classnames';

const DATE_FORMAT = 'YYYY-MM-DD';


/* This shows a button that summarizes the current range. When clicked, it
 * expands to a dual calendar date picker, with presets on the side. The
 * expanded window has an internal state that is prepolated with the string
 * values of the original dates, but it will not update the external state
 * until the apply button is pressed.
 *
 * The dates in the internal state are stored only as strings, not moment or
 * date objects. This causes it not to freak out when users are typing partial
 * dates. Where smart date objects (such as Date or Moment objects) are needed,
 * they should be created on the fly.
 */
export default class DateRangePicker extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            expanded: false,
            start: props.filters[this.props.startKey],
            end: props.filters[this.props.endKey],
        };
    }

    componentWillReceiveProps(newProps) {
        this.setState({
            start: newProps.filters[newProps.startKey],
            end: newProps.filters[newProps.endKey],
        });
    }

    expand() {
        var {expanded} = this.state;
        expanded = !expanded;
        this.setState({expanded});
    }

    updateDates({start, end}) {
        var newState = {};
        if (start !== undefined) {
            newState.start = start;
        }
        if (end !== undefined) {
            newState.end = end;
        }
        this.setState(newState);
    }

    validateDates() {
        let start = moment(this.state.start).startOf('day');
        let end = moment(this.state.end).endOf('day');
        if (!start.isValid() || !end.isValid()) {
            return [false, 'Invalid date format.'];
        }
        if (start.isAfter(end)) {
            return [false, 'Start comes after end.'];
        }
        return [true, null];
    }

    commit() {
        this.props.setFilters({
            [this.props.startKey]: this.state.start,
            [this.props.endKey]: this.state.end,
        });
        this.setState({expanded: false});
    }

    cancel() {
        console.log('closing');
        this.setState({
            expanded: false,
            start: this.props.filters[this.props.startKey],
            end: this.props.filters[this.props.endKey],
        });
    }

    render() {
        var [isValid, error] = this.validateDates();
        return (
            <div className="date-range-picker">
                <DateRangeSummaryButton
                    start={this.props.filters[this.props.startKey]}
                    end={this.props.filters[this.props.endKey]}
                    onClick={this.expand.bind(this)}
                    summaryDateFormat={this.props.summaryDateFormat}/>
                {this.state.expanded
                    ? <DateRangeDetail
                        start={this.state.start}
                        end={this.state.end}
                        min={this.props.min}
                        max={this.props.max}
                        valid={isValid}
                        error={error}
                        updateDates={this.updateDates.bind(this)}
                        commit={this.commit.bind(this)}
                        cancel={this.cancel.bind(this)}/>
                    : null}
            </div>
        )
    }
}

function isAMoment(props, propName, componentName) {
    let obj = props[propName];
    if (obj == undefined) {
        return;
    }
    if (!obj._isAMomentObject) {
        return new Error(`${componentName}.${propName} is required to be a Moment object.`);
    }
}
isAMoment.isRequired = function(props, propName, componentName) {
    var obj = props[propName];
    if (obj === undefined) {
        return new Error(`${componentName}.${propName} is a required property.`);
    }
    return isAMoment(props, propName);
}

DateRangePicker.propTypes = {
    filters: React.PropTypes.object.isRequired,
    setFilters: React.PropTypes.func.isRequired,
    startKey: React.PropTypes.string,
    endKey: React.PropTypes.string.isRequired,
    summaryDateFormat: React.PropTypes.string,
    min: isAMoment,
    max: isAMoment,
};

DateRangePicker.defaultProps = {
    startKey: 'startdate',
    endKey: 'enddate',
    summaryDateFormat: 'MMM D, YYYY',
};


/* This summarizes the date range. It uses the external value, not the internal
 * state, and so will only update when "Apply" is clicked. Clicking this causes
 * the detail window to expand.
 */
class DateRangeSummaryButton extends React.Component {
    getSummary() {
        var start = moment(this.props.start);
        var end = moment(this.props.end);
        var fmt = this.props.summaryDateFormat;
        return `${start.format(fmt)} - ${end.format(fmt)}`;
    }

    render() {
        return (
            <div className="summary-button" onClick={this.props.onClick}>
                <Icon name="calendar"/>
                <span className="summary">{this.getSummary()}</span>
                <Icon name="caret-down"/>
            </div>
        )
    }
}


/* This is the window that expands when the summary button is clicked. It
 * presents two calendars to choose dates, a list of presets, a raw text
 * field for the internal state's dates, and buttons to apply the changes
 * or cancel and close the window.
 */
class DateRangeDetail extends React.Component {
    handleChange(ev) {
        var name = ev.target.name;
        var value = ev.target.value;
        this.props.updateDates({[name]: value});
    }

    render() {
        return (
            <div className="detail-window">
                <div className="row">
                    <Calendar date={this.props.start}
                        min={this.props.min}
                        max={this.props.max}
                        onChange={(date) => this.props.updateDates({start: date})}/>
                    <Calendar date={this.props.end}
                        min={this.props.min}
                        max={this.props.max}
                        onChange={(date) => this.props.updateDates({end: date})}/>
                    <PresetRanges start={this.props.start} end={this.props.end} updateDates={this.props.updateDates}/>
                </div>

                <div className="row">
                    <div className="input-label-group">
                        <label>From</label>
                        <input name="start" value={this.props.start} onChange={this.handleChange.bind(this)}/>
                    </div>

                    <div className="input-label-group">
                        <label>To</label>
                        <input name="end" value={this.props.end} onChange={this.handleChange.bind(this)}/>
                    </div>

                    {this.props.valid
                        ? null
                        : <div className="errors">Error: {this.props.error}</div>
                    }

                    <div className="actions">
                        <button className="btn" onClick={this.props.cancel}>Cancel</button>
                        <button className="btn btn-submit" disabled={!this.props.valid} onClick={this.props.commit}>
                            Apply
                        </button>
                    </div>
                </div>
            </div>
        );
    }
}


/* This shows a Pikaday calendar, and updates the parent state when clicked.
 *
 * This has to deal with a lot of React lifetime events, because Pikaday does
 * not follow the React render model. Boo. The general gist of it is anytime
 * the component should render, it does a basically no-op render, and updates
 * the Pikaday element.
 */
class Calendar extends React.Component {
    constructor(props) {
        super(props);
        this.picker = null;
    }

    handleSelect(date) {
        this.props.onChange(moment(date).format(DATE_FORMAT));
    }

    componentDidMount() {
        var opts = {
            bound: false,
            container: this.refs.calendar.getDOMNode(),
            field: this.refs.textbox.getDOMNode(),
            onSelect: this.handleSelect.bind(this),
        }
        if (this.props.min) {
            opts.minDate = moment(this.min).toDate();
        }
        if (this.props.max) {
            opts.maxDate = moment(this.max).toDate();
        }
        this.picker = new Pikaday(opts);
        this.picker.setDate(moment(this.props.date).toDate(), true);
    }

    componentWillUnmount() {
        this.picker.destroy();
    }

    render() {
        if (this.picker) {
            this.picker.setDate(moment(this.props.date).toDate(), true);
        }
        return (
            <div className="calendar">
                <div ref="calendar"></div>
                {/* This input is only to make Pikaday work, it is not visible or used. */}
                <input type="text" ref="textbox"/>
            </div>
        );
    }
}


/* This shows a list of presets, highlighting any that match the current state.
 * When clicked, each state will update the internal state of the picker to match.
 */
class PresetRanges extends React.Component {
    handleClick(preset) {
        this.props.updateDates({
            start: preset.start.format(DATE_FORMAT),
            end: preset.end.format(DATE_FORMAT),
        });
    }

    render() {
        var start = moment(this.props.start);
        var end = moment(this.props.end);

        var today = moment().startOf('day');
        var lastMonth = moment(today).subtract(1, 'month').startOf('month');
        var daysAgo = (n) => moment(today).subtract(n, 'days');

        var presets = [
            {title: "Today", start: today, end: today},
            {title: "Yesterday", start: daysAgo(1), end: daysAgo(1)},
            {title: "Last 7 days", start: daysAgo(7), end: today},
            {title: "Last 30 days", start: daysAgo(30), end: today},
            {title: "Last 90 days", start: daysAgo(90), end: today},
            {title: "This month", start: moment(today).startOf('month'), end: moment(today).endOf('month')},
            {title: "Last month", start: lastMonth, end: moment(lastMonth).endOf('month')},
        ];

        return (
            <ul className="preset-picker">
                {presets.map((preset) => {
                    var selected;
                    if (start.isValid() && end.isValid()) {
                        selected = (moment(this.props.start).isSame(preset.start, 'day') &&
                                    moment(this.props.end).isSame(preset.end, 'day'));
                    } else {
                        selected = false;
                    }
                    var className = cx('preset', {selected: selected});
                    return <li className={className}
                               key={preset.title}
                               onClick={this.handleClick.bind(this, preset)}>
                        {preset.title}
                    </li>;
                })}
            </ul>
        );
    }
}
