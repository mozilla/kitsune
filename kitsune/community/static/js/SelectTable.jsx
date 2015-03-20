import {Icon} from './contributors-common.jsx';

function cssifyName(name) {
    return name.replace(/_/g, '-');
}

export default class SelectTable extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            selections: props.contributors.map(function() { return false; })
        }
    }

    componentWillReceiveProps(newProps) {
        var {selections} = this.state;
        for (var i = 0; i < newProps.contributors.length; i++) {
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
        if (this.props.contributors.length > 0) {
            return <div>
                <table className="top-contributors">
                    <SelectTableHeader
                        selections={this.state.selections}
                        onSelectAll={this.handleSelectAll.bind(this)}
                        columns={this.props.columns}/>
                    <SelectTableBody
                        contributors={this.props.contributors}
                        selections={this.state.selections}
                        onSelect={this.handleSelection.bind(this)}
                        columns={this.props.columns}/>
                </table>
            </div>;
        } else {
            return <h2>No contributors match filters.</h2>;
        }
    }
}

class SelectTableHeader extends React.Component {
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
                    {this.props.columns.map((info) => (
                        <th key={info.key} data-column={cssifyName(info.key)}>
                            {info.title}
                        </th>
                    ))}
                    <th data-column="actions">Actions</th>
                </tr>
            </thead>
        );
    }
}

class SelectTableBody extends React.Component {
    render() {
        return (
            <tbody>
                {this.props.contributors.map(function(contributor, i) {
                    return <SelectTableRow
                        selected={this.props.selections[i]}
                        onSelect={(val) => this.props.onSelect(i, val)}
                        key={contributor.user.username}
                        columns={this.props.columns}
                        {...contributor}/>;
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
                    <td key={info.key} data-column={cssifyName(info.key)}>
                        {(info.transform || (d) => d)(this.props[info.key])}
                    </td>
                ))}
                <td data-column="actions">
                    <Icon name="paper-plane"/>
                </td>
            </tr>
        );
    }
}
