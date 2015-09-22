/*
A tabs implementation for React using ES6 syntax. Does only the bare minimum
that is required of tabs.

This component is stateless. The index of the currently active tab needs to
be saved in the state of your app, and passed as a prop called `index`.
Children must be instances of the `Tab` component.
*/

class TabNav extends React.Component {
  render() {
    var tabClass = 'sumo-tabs-nav-inactive';

    if (this.props.active) {
      tabClass = 'sumo-tabs-nav-active';
    }

    return (
      <li
          data-index={this.props.index}
          key={'tabs-nav-link-' + this.props.index}
          onClick={this.props.switchTab}
          className={'sumo-tabs-nav-link ' + tabClass}
        >
        {this.props.children}
      </li>
    );
  }
}


export class Tab extends React.Component {
  render() {
    var tabClass = 'sumo-tabs-tab-hidden';
    var style = {
      display: 'none'
    };

    if (this.props.visible) {
      tabClass = 'sumo-tabs-tab-visible';
      style.display = 'block';
    }

    return (
      <section className={'sumo-tabs-tab ' + tabClass} style={style}>
        {this.props.children}
      </section>
    );
  }
}


export class Tabs extends React.Component {
  _switchTab(index, e) {
    this.props.onSelect(index);
  }

  render() {
    var activeIndex = this.props.index;
    var navLinks = [];
    var tabsContent = [];

    React.Children.forEach(this.props.children, (elem, i) => {
      var title = elem.props.title;
      var active = false;

      if (i === activeIndex) {
        active = true;
      }

      navLinks.push(
        <TabNav
          index={i}
          active={active}
          switchTab={this._switchTab.bind(this, i)}
          key={'tabs-nav-' + i}
        >
          {title}
        </TabNav>
      );

      tabsContent.push(
        <Tab index={i} key={'tabs-content-tab-' + i} visible={active}>
          {elem.props.children}
        </Tab>
      );
    });

    return (
      <div className="sumo-tabs">
        <nav className="sumo-tabs-nav">
          <ul>
            {navLinks}
          </ul>
        </nav>

        <div className="sumo-tabs-content">
          {tabsContent}
        </div>
      </div>
    );
  }
}

Tabs.propTypes = {
  index: React.PropTypes.number.isRequired,
  onSelect: React.PropTypes.func.isRequired,
  children: React.PropTypes.oneOfType([
    React.PropTypes.instanceOf(Tab),
    React.PropTypes.arrayOf(Tab),
  ]),
};


export default {
  Tabs,
  Tab,
}
