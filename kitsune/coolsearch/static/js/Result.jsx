export default class Result extends React.Component {
    render() {
        return (
            <article className={"result " + this.props.type}>
                <h3><a className="title" href="">{this.props.title}</a></h3>
                <a href="">{this.props.content}</a>
            </article>
        );
    }
}
