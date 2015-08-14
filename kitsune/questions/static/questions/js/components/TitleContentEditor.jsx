/* globals React:false */
import AAQStep from './AAQStep.jsx';
import AAQActions from '../actions/AAQActions.es6.js';

export default class TitleContentEditor extends AAQStep {
  handleChange(ev) {
    let {name, value} = ev.target;
    if (name === 'title') {
      AAQActions.setTitle(value);
    } else if (name === 'content') {
      AAQActions.setContent(value);
    } else {
      throw new Error(`Unknown field name ${name} in TitleContentEditor.`);
    }
  }

  shouldExpand() {
    return (this.props.question.topic !== null &&
            this.props.question.product !== null);
  }

  heading() {
    return 'Provide details about your question.';
  }

  body() {
    return (
      <div className="AAQApp__TitleContentEditor">
        <div className="row">
          <div className="AAQApp__TitleContentEditor__Editor">
            <div className="AAQApp__TitleContentEditor__Editor__Title">
              <label>Subject</label>
              <input
                type="text"
                name="title"
                value={this.props.question.title}
                onChange={this.handleChange.bind(this)}
                ref="title"/>
            </div>
            <div className="AAQApp__TitleContentEditor__Editor__Content">
              <label>More Details</label>
              <textarea
                name="content"
                value={this.props.question.content}
                onChange={this.handleChange.bind(this)}
                ref="content"/>
            </div>
          </div>
          <SuggestionList suggestions={this.props.suggestions}/>
        </div>

        <div className="row">
          <TroubleshootingData {...this.props.troubleshooting}/>
        </div>
      </div>
    );
  }
}
TitleContentEditor.propTypes = {
  className: React.PropTypes.string,
  question: React.PropTypes.object.isRequired,
  suggestions: React.PropTypes.array.isRequired,
  troubleshooting: React.PropTypes.object.isRequired,
};

class SuggestionList extends React.Component {
  render() {
    return (
      <div className="AAQApp__SuggestionList">
        <h3>Do any of these articles answer your question?</h3>
        <ul>
          {this.props.suggestions.map((suggestion) => (
            <SuggestionItem key={suggestion.slug} suggestion={suggestion}/>))}
        </ul>
      </div>
    );
  }
}
SuggestionList.propTypes = {
  suggestions: React.PropTypes.array.isRequired,
};

class SuggestionItem extends React.Component {
  render() {
    let suggestion = this.props.suggestion;
    return (
      <li className="AAQApp__SuggestionList__SuggestionItem">
        <a href={suggestion.url}>{suggestion.title}</a>
        <div dangerouslySetInnerHTML={{__html: suggestion.summary}}/>
      </li>
    );
  }
}
SuggestionItem.propTypes = {
  suggestion: React.PropTypes.object.isRequired,
};

class TroubleshootingData extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      expand: false,
    };
  }

  handleOpt({target: {checked}}) {
    AAQActions.setTroubleshootingOptIn(checked);
  }

  toggleExpand(ev) {
    ev.preventDefault();
    this.setState(state => ({expand: !this.state.expand}));
  }

  render() {
    return (
      <div className="AAQApp__TroubleshootingData">
        <h3>Troubleshooting Information</h3>
        <p>
          This information gives details about the internal workings of
          your browser that will help in answering your question.
        </p>
        <p>
          <input type="checkbox"
                 name="troubleshootingDataOptIn"
                 checked={this.props.optIn}
                 onChange={this.handleOpt.bind(this)}>
            <label>Share data</label>
          </input>
          <a href="#" onClick={this.toggleExpand.bind(this)}>
            {this.props.optIn
              ? (this.state.expand
                ? 'Hide'
                : "Show the data I'm sharing")
              : null}
          </a>
        </p>
        {this.state.expand && this.props.optIn
          ? <pre className="AAQApp__TroubleshootingData__dataView">
              {JSON.stringify(this.props.data, null, 2)}
            </pre>
          : null}
      </div>
    );
  }
}
TroubleshootingData.propTypes = {
  optIn: React.PropTypes.bool.isRequired,
  data: React.PropTypes.object.isRequired,
}
