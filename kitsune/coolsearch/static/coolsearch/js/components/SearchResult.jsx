export default class SearchResult extends React.Component {
  render() {
    return (
      <article className={"result " + this.props.data.type}>
        <h3><a className="title" href={this.props.data.url}>{this.props.data.title}</a></h3>
        <a href={this.props.data.url}>{this.props.data.content}</a>
      </article>
    );
  }
}
