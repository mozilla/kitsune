/*
A tabs implementation for React using ES6 syntax. Does only the bare minimum
that is required of tabs.
*/

class TabNav extends React.Component {
  constructor(props) {
    super(props);
  }

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
  constructor(props) {
    super(props);
  }

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
  constructor(props) {
    super(props);

    var self = this;

    var navLinks = [];
    var tabsContent = [];

    var index = this.props.index;

    if (!Number.isInteger(this.props.index) || this.props.index < 0) {
      index = 0;
    }

    this.state = {
      index: index
    };

    // Generate navigation and content.
    this.props.children.forEach(function (elem, i) {
      if (elem.type !== Tab) {
        return;
      }

      var title = elem.props.title;
      navLinks.push(
        <TabNav
          index={i}
          active={false}
          switchTab={self._switchTab.bind(self)}
        >
          {title}
        </TabNav>
      );

      tabsContent.push(
        <Tab index={i} key={'tabs-content-tab-' + i}>
          {elem.props.children}
        </Tab>
      );
    });

    this.navLinks = navLinks;
    this.tabsContent = tabsContent;
  }

  _getNavLinks(activeIndex) {
    var self = this;
    return this.navLinks.map(function (elem, i) {
      var active = false;
      var index = elem.props.index;

      if (index === activeIndex) {
        active = true;
      }

      return (
        <TabNav
          index={index}
          active={active}
          switchTab={self._switchTab.bind(self)}
        >
          {elem.props.children}
        </TabNav>
      );
    });
  }

  _getTabsContent(activeIndex) {
    return this.tabsContent.map(function (elem, i) {
      var visible = false;

      if (elem.props.index === activeIndex) {
        visible = true;
      }

      return (
        <Tab index={i} key={'tabs-content-tab-' + i} visible={visible}>
          {elem.props.children}
        </Tab>
      );
    });
  }

  _switchTab(e) {
    var index = parseInt(e.target.dataset.index);
    this._showTab(index);
    if (typeof(this.props.onSelect) === 'function') {
      this.props.onSelect(index);
    }
  }

  _showTab(index) {
    this.setState({
      index: index
    });
  }

  render() {
    var activeIndex = this.state.index;
    var navLinks = this._getNavLinks(activeIndex);
    var tabsContent = this._getTabsContent(activeIndex);

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


export default {
  Tabs,
  Tab,
}
