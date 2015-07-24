/* globals React:false */

export class Errors extends React.Component {
  render() {
    let formattedErrors = [];
    for (let key in this.props.errors) {
      let prefix = `${key}: `;
      if (key[0] === '_') {
        prefix = '';
      }
      for (let error of this.props.errors[key]) {
        formattedErrors.push(`${prefix}${error}`);
      }
    }
    return (
      <ul className="Errors">
        {formattedErrors.map((error, i) => <li key={`error-${i}`}>{error}</li>)}
      </ul>
    );
  }
}
Errors.propTypes = {
  errors: React.PropTypes.object.isRequired,
};


export default {
  Errors,
};
