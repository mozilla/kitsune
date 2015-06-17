import {locales, products} from './contributors-common.jsx';
import DateRangePicker from './DateRangePicker.jsx';
import AdvancedFilters from './AdvancedFilters.jsx';

export default class CommunityFilters extends React.Component {
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

    render() {
        return <div className="Filters">
            <input
                className="Filters__item"
                name="username"
                autoComplete="off"
                defaultValue={this.props.filters.username}
                onChange={this.handleChange.bind(this)}
                placeholder="Filter by username"/>

            <DateRangePicker max={moment()} setFilters={this.props.setFilters} filters={this.props.filters} />

            <select className="Filters__item"
                    name="locale"
                    defaultValue={this.props.filters.locale}
                    onChange={this.handleChange.bind(this)}>
                <option value="">Select a locale</option>
                {locales.map(([name, code]) => <option key={code} value={code}>{name}</option>)}
            </select>

            <select name="product" defaultValue={this.props.filters.product} onChange={this.handleChange.bind(this)}>
                <option value="">Select a product</option>
                {products.map((prod) => <option key={prod.slug} value={prod.slug}>{prod.title}</option>)}
            </select>

            <AdvancedFilters {...this.props}/>
        </div>;
    }
}
