/* globals React:false */
import cx from 'classnames';

import QuestionEditStore from '../stores/QuestionEditStore.es6.js';
import AAQActions from '../actions/AAQActions.es6.js';
import scrollTo from '../../../sumo/js/utils/scrollTo.es6.js';
import {questionEditState} from '../constants/AAQConstants.es6.js';


const products = JSON.parse(document.querySelector('.data[name=products]').innerHTML);
const topics = JSON.parse(document.querySelector('.data[name=topics]').innerHTML);


export default class AAQApp extends React.Component {
  constructor(props) {
    super(props);
    this.state = this.getStateFromStores();
  }

  componentDidMount() {
    QuestionEditStore.addChangeListener(() => {
      this.setState(this.getStateFromStores());
    });
  }

  getStateFromStores() {
    return {
      question: QuestionEditStore.getQuestion(),
      suggestions: QuestionEditStore.getSuggestions(),
      validationErrors: QuestionEditStore.getValidationErrors(),
      questionState: QuestionEditStore.getState(),
    };
  }

  render() {
    return (
      <div className="AAQApp">
        <ProductSelector {...this.state}/>
        <TopicSelector {...this.state}/>
        <TitleContentEditor {...this.state}/>
        <SubmitQuestion {...this.state}/>
      </div>
    );
  }
}


class AAQStep extends React.Component {
  render() {
    let heading = this.heading();
    return (
      <div className="AAQApp__Step highlight-box">
        {heading
          ? <h2>{heading}</h2>
          : null}
        {this.shouldExpand()
          ? this.body()
          : null}
      </div>
    );
  }

  scrollToNextStep() {
    let currentStep = React.findDOMNode(this); // will throw if not mounted
    let nextStep = currentStep.nextElementSibling;
    if (nextStep === null) {
      throw 'Tried to call scrollToNextStep(), but this is the last step.';
    }
    if (!nextStep.classList.contains('AAQApp__Step')) {
      throw 'Tried to call scrollToNextStep(), but the next element is not an AAQStep.';
    }
    scrollTo(nextStep);
  }
}
AAQStep.propTypes = {
  question: React.PropTypes.object.isRequired,
};


class ProductSelector extends AAQStep {
  shouldExpand() {
    // The Product selector is always visible.
    return true;
  }

  heading() {
    return 'Which product would you like to ask a question about?';
  }

  body() {
    return (
      <ul id="product-picker" className="AAQApp__ProductSelector card-grid cf">
        {products.map((product) => {
          const selected = (this.props.question.product === product.slug);
          return <ProductCard
            key={product.slug}
            product={product}
            selected={selected}
            scrollToNextStep={this.scrollToNextStep.bind(this)}/>;
        })}
      </ul>
    );
  }
}


class ProductCard extends React.Component {
  handleSelect(ev) {
    ev.preventDefault();
    AAQActions.setProduct(this.props.product.slug);
    this.props.scrollToNextStep();
  }

  render() {
    let className = cx('AAQApp__ProductSelector__ProductCard', {selected: this.props.selected});
    return (
      <li onClick={this.handleSelect.bind(this)} className={className}>
        <a href="#">
          <img src={this.props.product.image}/>
          <span className="title">{this.props.product.title}</span>
          <span className="description">{this.props.product.description}</span>
        </a>
      </li>
    );
  }
}
ProductCard.propTypes = {
  product: React.PropTypes.object.isRequired,
  selected: React.PropTypes.bool.isRequired,
};


class TopicSelector extends AAQStep {
  shouldExpand() {
    return !!this.props.question.product;
  }

  heading() {
    return 'Which topic best describes your question?';
  }

  body() {
    return (
      <ul className="AAQApp__TopicSelector">
        {topics.filter((t) => t.product === this.props.question.product)
          .map((topic) => {
            var selected = this.props.question.topic === topic.slug;
            return <TopicItem
              key={topic.slug}
              topic={topic}
              selected={selected}
              scrollToNextStep={this.scrollToNextStep.bind(this)}/>;
          })}
      </ul>
    );
  }
}


class TopicItem extends React.Component {
  handleSelect(ev) {
    ev.preventDefault();
    AAQActions.setTopic(this.props.topic.slug);
    this.props.scrollToNextStep();
  }

  render() {
    let className = cx('AAQApp__TopicSelector__Topic', {selected: this.props.selected});
    return (
      <li onClick={this.handleSelect.bind(this)} className={className}>
        {this.props.topic.title} ({this.props.topic.slug})
      </li>
    );
  }
}
TopicItem.propTypes = {
  topic: React.PropTypes.object.isRequired,
  selected: React.PropTypes.bool.isRequired,
};



class TitleContentEditor extends AAQStep {
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


class SubmitQuestion extends AAQStep {
  handleSubmit() {
    AAQActions.submitQuestion();
  }

  shouldExpand() {
    return true;
  }

  heading() {
    return null;
  }

  body() {
    let buttonTexts = {
      [questionEditState.INVALID]: 'Submit',
      [questionEditState.VALID]: 'Submit',
      [questionEditState.PENDING]: 'Submitting...',
      [questionEditState.SUBMITTED]: 'Done!',
      [questionEditState.ERROR]: 'Error!',
    };

    return (
      <div>
        <pre>
          {JSON.stringify(this.props.question, null, 2)}
        </pre>
        <button className="btn btn-submit"
                onClick={this.handleSubmit}
                disabled={this.props.questionState !== questionEditState.VALID}>
          {buttonTexts[this.props.questionState]}
        </button>
        <pre>
          {this.props.questionState}<br/>
          {this.props.validationErrors}
        </pre>
      </div>
    );
  }
}
