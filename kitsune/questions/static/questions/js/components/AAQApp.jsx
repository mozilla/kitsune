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
    return (
      <div className="AAQApp">
        <ProductSelector question={this.state.question}/>
        <TopicSelector question={this.state.question}/>
        <TitleContentEditor question={this.state.question}/>
      </div>
    );
  }
}


class ProductSelector extends React.Component {
  render() {
    return (
      <div className="AAQApp__ProductSelector">
        <h2>Which product would you like to ask a question about?</h2>
        <ul id="product-picker" className="card-grid cf">
          {products.map((product) => {
            const selected = (this.props.question.product === product.slug);
            return <ProductCard key={product.slug} product={product} selected={selected} />;
          })}
        </ul>
      </div>
    );
  }
}
ProductSelector.propTypes = {
  question: React.PropTypes.object.isRequired,
};

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

class TopicSelector extends React.Component {
  render() {
    if (this.props.question.product === null) {
      return (
        <div className="AAQApp__TopicSelector">
          <h3>Pick a product first.</h3>
        </div>
      );
    } else {
      return (
        <div className="AAQApp__TopicSelector">
          <h2>Which category best describes your problem?</h2>
          <ul>
            {topics.filter((t) => t.product === this.props.question.product)
              .map((topic) => {
                var selected = this.props.question.topic === topic.slug;
                return <TopicItem key={topic.slug} topic={topic} selected={selected}/>;
              })}
          </ul>
        </div>
      );
    }
  }
}
TopicSelector.propTypes = {
  question: React.PropTypes.object.isRequired,
};

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

class TitleContentEditor extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      title: this.props.question.title,
    };
  }

  handleChange(ev) {
    console.log('change!');
  }

  handleBlur(ev) {
    console.log('blur!');
  }

  render() {
    return (
      <div className="AAQApp__TitleContentEditor">
        <input
          type="text"
          name="title"
          value={this.props.question.title}
          onChange={this.handleChange.bind(this)}
          onBlur={this.handleBlur.bind(this)}/>
        <textarea
          name="content"
          value={this.props.question.content}
          onChange={this.handleChange.bind(this)}
          onBlur={this.handleBlur.bind(this)}/>
      </div>
    );
  }
}
TitleContentEditor.propTypes = {
  question: React.PropTypes.object.isRequired,
};
