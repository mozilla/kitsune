/* globals React:false */
/* ecmaFeatures jsx: true */
import QuestionEditStore from '../stores/QuestionEditStore.es6.js';
import UserAuthStore from '../../../users/js/stores/UserAuthStore.es6.js';
import ProductSelector from './ProductSelector.jsx';
import TopicSelector from './TopicSelector.jsx';
import TitleContentEditor from './TitleContentEditor.jsx';
import UserAuth from './UserAuth.jsx';
import SubmitQuestion from './SubmitQuestion.jsx';

export default class AAQApp extends React.Component {
  constructor(props) {
    super(props);
    this.state = this.getStateFromStores();
  }

  componentDidMount() {
    QuestionEditStore.addChangeListener(() => {
      this.setState(this.getStateFromStores());
    });
    UserAuthStore.addChangeListener(() => {
      this.setState(this.getStateFromStores());
    });
  }

  getStateFromStores() {
    return {
      question: QuestionEditStore.getQuestion(),
      suggestions: QuestionEditStore.getSuggestions(),
      validationErrors: QuestionEditStore.getValidationErrors(),
      questionState: QuestionEditStore.getState(),
      userAuth: UserAuthStore.getAll(),
    };
  }

  render() {
    return (
      <div className="AAQApp">
        <ProductSelector {...this.state}/>
        <TopicSelector {...this.state}/>
        <TitleContentEditor {...this.state}/>
        <UserAuth userAuth={this.state.userAuth}/>
        <SubmitQuestion {...this.state}/>
      </div>
    );
  }
}
