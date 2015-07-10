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
    );
  }
}
TitleContentEditor.propTypes = {
  className: React.PropTypes.string,
  question: React.PropTypes.object.isRequired,
  suggestions: React.PropTypes.array.isRequired,
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
