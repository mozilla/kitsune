/* globals React:false */
import cx from 'classnames';
import AAQStep from './AAQStep.jsx';
import AAQActions from '../actions/AAQActions.es6.js';

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
                scrollToNextStep={this.scrollToNextStep.bind(this)}/>
            );
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
  scrollToNextStep: React.PropTypes.func.isRequired,
};
