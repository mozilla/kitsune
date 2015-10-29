/* globals React:false */
import cx from 'classnames';
import AAQStep from './AAQStep.jsx';
import AAQActions from '../actions/AAQActions.es6.js';
import aaqGa from '../utils/aaqGa.es6.js';

const topics = JSON.parse(document.querySelector('.data[name=topics]').innerHTML);

export default class TopicSelector extends AAQStep {
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
            return (
              <TopicItem
                key={topic.slug}
                topic={topic}
                selected={selected}
                switchToNextStep={this.switchToNextStep.bind(this)}/>
            );
          })}
      </ul>
    );
  }
}


class TopicItem extends React.Component {
  handleSelect(ev) {
    ev.preventDefault();
    let slug = this.props.topic.slug;
    aaqGa.trackEvent('topic selected', slug);
    AAQActions.setTopic(slug);
    this.props.switchToNextStep();
  }

  render() {
    let className = cx('AAQApp__TopicSelector__Topic', {selected: this.props.selected});
    return (
      <li onClick={this.handleSelect.bind(this)} className={className}>
        <h3>{this.props.topic.title}</h3>
        <p>{this.props.topic.description}</p>
      </li>
    );
  }
}
TopicItem.propTypes = {
  topic: React.PropTypes.object.isRequired,
  selected: React.PropTypes.bool.isRequired,
  switchToNextStep: React.PropTypes.func.isRequired,
};
