/* globals React:false */
import cx from 'classnames';
import AAQStep from './AAQStep.jsx';
import AAQActions from '../actions/AAQActions.es6.js';

const products = JSON.parse(document.querySelector('.data[name=products]').innerHTML);

export default class ProductSelector extends AAQStep {
  heading() {
    return 'Which product would you like to ask a question about?';
  }

  body() {
    return (
      <ul id="product-picker" className="AAQApp__ProductSelector card-grid cf">
        {products.map((product) => {
          const selected = (this.props.question.product === product.slug);
          return (
            <ProductCard
              key={product.slug}
              product={product}
              selected={selected}
              switchToNextStep={this.switchToNextStep.bind(this)}/>
          );
        })}
      </ul>
    );
  }
}

class ProductCard extends React.Component {
  handleSelect(ev) {
    ev.preventDefault();
    AAQActions.setProduct(this.props.product.slug);
    this.props.switchToNextStep();
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
  switchToNextStep: React.PropTypes.func.isRequired,
};
