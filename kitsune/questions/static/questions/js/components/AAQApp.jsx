/* globals React:false */
import cx from 'classnames';

import QuestionEditStore from '../stores/QuestionEditStore.es6.js';
import AAQActions from '../actions/AAQActions.es6.js';


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
      question: QuestionEditStore.get(),
    };
  }

  render() {
    console.log('AAQApp::render()');
    return (
      <div className="AAQApp">
        <ProductSelector question={this.state.question}/>
        <TopicSelector question={this.state.question}/>
        <TitleContentEditor question={this.state.question}/>
        <SubmitQuestion question={this.state.question}/>
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
      <ul id="product-picker" className="card-grid cf">
        {products.map((product) => {
          const selected = (this.props.question.product === product.slug);
          return <ProductCard key={product.slug} product={product} selected={selected} />;
        })}
      </ul>
    );
  }
}


class ProductCard extends React.Component {
  handleSelect(ev) {
    ev.preventDefault();
    AAQActions.setProduct(this.props.product.slug);
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
      <ul>
        {topics.filter((t) => t.product === this.props.question.product)
          .map((topic) => {
            var selected = this.props.question.topic === topic.slug;
            return <TopicItem key={topic.slug} topic={topic} selected={selected}/>;
          })}
      </ul>
    );
  }
}


class TopicItem extends React.Component {
  handleSelect(ev) {
    ev.preventDefault();
    AAQActions.setTopic(this.props.topic.slug);
  }

  render() {
    let className = cx('AAQApp__TopicSelector__Topic', {selected: this.props.selected});
    return (
      <li onClick={this.handleSelect.bind(this)} className={className}>
        {this.props.topic.title}
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
      <div>
        <p>
          <label>Subject</label>
          <input
            type="text"
            name="title"
            value={this.props.question.title}
            onChange={this.handleChange.bind(this)}
            onBlur={this.handleChange.bind(this)}/>
        </p>
        <p>
          <label>More Details</label>
          <textarea
            name="content"
            value={this.props.question.content}
            onChange={this.handleChange.bind(this)}
            onBlur={this.handleChange.bind(this)}/>
        </p>
      </div>
    );
  }
}

class SubmitQuestion extends AAQStep {
  shouldExpand() {
    return true;
  }

  heading() {
    return null;
  }

  body() {
    return (
      <pre>
        {JSON.stringify(this.props.question, null, 2)}
      </pre>
    );
  }
}
