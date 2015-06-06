import cx from 'classnames';
import {Icon} from './contributors-common.jsx';

export default class SelectTable extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            selections: props.data.map(function() { return false; })
        }
    }

    componentWillReceiveProps(newProps) {
        var {selections} = this.state;
        for (var i = 0; i < newProps.data.length; i++) {
            selections[i] = !!selections[i];
        }
        this.setState({selections});
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
        if (this.props.data.length > 0) {
            return <div className="SelectTable">
                <table className="top-contributors">
                    <SelectTableHeader
                        selections={this.state.selections}
                        onSelectAll={this.handleSelectAll.bind(this)}
                        columns={this.props.columns}
                        filters={this.props.filters}
                        setFilters={this.props.setFilters}
                        allowedOrderings={this.props.allowedOrderings}
                        actions={this.props.actions}/>
                    <SelectTableBody
                        data={this.props.data}
                        selections={this.state.selections}
                        onSelect={this.handleSelection.bind(this)}
                        columns={this.props.columns}
                        actions={this.props.actions}/>
                </table>
                <SelectTableActionBox
                    actions={this.props.actions}
                    selected={this.props.data.filter((data, i) => this.state.selections[i])}/>
            </div>;
        } else {
            return <h2>No contributors match filters.</h2>;
        }
    }
}

SelectTable.propTypes = {
    data: React.PropTypes.arrayOf(React.PropTypes.object).isRequired,
    columns: React.PropTypes.arrayOf(React.PropTypes.object).isRequired,
    setFilters: React.PropTypes.func.isRequired,
    filters: React.PropTypes.object.isRequired,
    allowedOrderings: React.PropTypes.arrayOf(React.PropTypes.string).isRequired,
    actions: React.PropTypes.arrayOf(React.PropTypes.object),
};

SelectTable.defaultProps = {
    actions: [],
};



class SelectTableHeader extends React.Component {
    handleSelectAll(ev) {
        ev.stopPropagation();
        this.props.onSelectAll(ev.target.checked);
    }

    handleSortClick(name, ev) {
        ev.preventDefault();
        this.props.setFilters({ordering: name});
    }

    render() {
        var allSelected = this.props.selections.reduce((a, b) => a && b, true);

        let sortState = (key) => {
            if (key === this.props.filters.ordering) {
                return 'ascending';
            } else if (`-${key}` === this.props.filters.ordering) {
                return 'descending';
            } else {
                return 'idle';
            }
        };

        return (
            <thead>
                <tr className="top-contributors-header">
                    <th data-column="select">
                        <input type="checkbox" ref="selectAll"
                            checked={allSelected}
                            onChange={this.handleSelectAll.bind(this)}/>
                    </th>
                    {this.props.columns.map((info) => {
                        var nextOrdering;
                        if (this.props.filters.ordering === `-${info.key}`) {
                            nextOrdering = info.key;
                        } else {
                            nextOrdering = `-${info.key}`;
                        }
                        var pageFilters = _.extend({}, this.props.filters, {ordering: nextOrdering});
                        var pageUrl = k.queryParamStringFromDict(pageFilters);

                        return (
                            <th key={info.key} data-column={info.key}>
                                {this.props.allowedOrderings.indexOf(info.key) >= 0
                                    ? (
                                        <a href={pageUrl} onClick={this.handleSortClick.bind(this, nextOrdering)}>
                                            {info.title}
                                            <SortWidget state={sortState(info.key)}/>
                                        </a>
                                    )
                                    : info.title
                                }
                            </th>
                        );
                    })}
                    {this.props.actions.length > 0
                        ? <th data-column="actions">Actions</th>
                        : null}
                </tr>
            </thead>
        );
    }
}

SelectTableHeader.propTypes = {
    selections: React.PropTypes.arrayOf(React.PropTypes.bool).isRequired,
    onSelectAll: React.PropTypes.func.isRequired,
    columns: React.PropTypes.arrayOf(React.PropTypes.object).isRequired,
    setFilters: React.PropTypes.func.isRequired,
    filters: React.PropTypes.object.isRequired,
    allowedOrderings: React.PropTypes.arrayOf(React.PropTypes.string).isRequired,
};


class SortWidget extends React.Component {
    render() {
        var state = this.props.state;
        if (state === 'ascending') {
            return <Icon className="sort-widget" name="sort-asc"/>;
        } else if (state === 'descending') {
            return <Icon className="sort-widget" name="sort-desc"/>;
        } else {
            return null;
        }
    }
}

SortWidget.propTypes = {
    state: React.PropTypes.oneOf(['ascending', 'descending', 'idle']).isRequired,
}


class SelectTableBody extends React.Component {
    render() {
        return (
            <tbody>
                {this.props.data.map(function(contributor, i) {
                    return <SelectTableRow
                        selected={this.props.selections[i]}
                        onSelect={(val) => this.props.onSelect(i, val)}
                        key={contributor.user.username}
                        columns={this.props.columns}
                        actions={this.props.actions}
                        data={contributor}/>;
                }.bind(this))}
            </tbody>
        );
    }
}

class SelectTableRow extends React.Component {
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
                {this.props.columns.map((info) => (
                    <td key={info.key} data-column={info.key}>
                        {(info.transform || (d) => d)(this.props.data[info.key])}
                    </td>
                ))}

                {this.props.actions.length > 0
                    ? (
                        <td data-column="actions">
                            {this.props.actions.map((action) => (
                                <span title={action.hover} onClick={(ev) => action.onClick([this.props.data])}>
                                    <Icon name={action.icon}/>
                                </span>
                            ))}
                        </td>
                    )
                    : null}
            </tr>
        );
    }
}


class SelectTableActionBox extends React.Component {
    render() {
        if (this.props.selected.length === 0) {
            return null;
        } else {
            console.log('SelectTableActionBox', this.props);
            return (
                <div className="SelectTable__actionBox">
                    <span className="SelectTable__actionBox__count">
                        {this.props.selected.length} users selected.
                    </span>
                    <span className="SelectTable__actionBox__actions">
                        {this.props.actions.map((action) => (
                            <span onClick={() => action.onClick(this.props.selected)}>
                                <Icon name={action.icon}/>
                                {action.hover}
                            </span>
                        ))}
                    </span>
                </div>
            );
        }
    }
}
