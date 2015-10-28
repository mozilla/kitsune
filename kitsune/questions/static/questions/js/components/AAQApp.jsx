/* globals React:false */
/* ecmaFeatures jsx: true */
import QuestionEditStore from '../stores/QuestionEditStore.es6.js';
import UserAuthStore from '../../../users/js/stores/UserAuthStore.es6.js';
import ProductSelector from './ProductSelector.jsx';
import TopicSelector from './TopicSelector.jsx';
import TitleContentEditor from './TitleContentEditor.jsx';
import UserAuth from './UserAuth.jsx';
import SubmitQuestion from './SubmitQuestion.jsx';
import TroubleshootingDataStore from '../stores/TroubleshootingDataStore.es6.js';
import UrlStore from '../../../sumo/js/stores/UrlStore.es6.js';
import UrlActions from '../../../sumo/js/actions/UrlActions.es6.js';
import {aaqGa} from '../utils/';

export default class AAQApp extends React.Component {
  constructor(props) {
    super(props);
    this.state = this.getStateFromStores();
    this.onChange = this.onChange.bind(this);
  }

  componentDidMount() {
    QuestionEditStore.addChangeListener(this.onChange);
    UserAuthStore.addChangeListener(this.onChange);
    TroubleshootingDataStore.addChangeListener(this.onChange);
    UrlStore.addChangeListener(this.onChange);

    UrlActions.updateQueryStringDefaults({step: 'product'});
    aaqGa.trackEvent('AAQ SPA loaded');
  }

  componentWillUnmount() {
    QuestionEditStore.removeChangeListener(this.onChange);
    UserAuthStore.removeChangeListener(this.onChange);
    TroubleshootingDataStore.removeChangeListener(this.onChange);
    UrlStore.removeChangeListener(this.onChange);
  }

  onChange() {
    this.setState(this.getStateFromStores());
  }

  getStateFromStores() {
    return {
      question: QuestionEditStore.getQuestion(),
      suggestions: QuestionEditStore.getSuggestions(),
      validationErrors: QuestionEditStore.getValidationErrors(),
      questionState: QuestionEditStore.getState(),
      userAuth: UserAuthStore.getAll(),
      troubleshooting: TroubleshootingDataStore.getAll(),
      step: UrlStore.get('step'),
    };
  }

  setStep(step) {
    UrlActions.updateQueryString({step});
  }

  render() {
    return (
      <div className="AAQApp">
        {(() => {
          switch (this.state.step) {
            case 'product':
              return <ProductSelector {...this.state} setStep={this.setStep.bind(this, 'topic')}/>;
            case 'topic':
              return <TopicSelector {...this.state} setStep={this.setStep.bind(this, 'title')}/>;
            case 'title':
              return [
                <TitleContentEditor {...this.state}/>,
                <UserAuth userAuth={this.state.userAuth}/>
              ];
            case undefined:
              return '...';
            default:
              throw new Error(`Unknown AAQ step: ${this.state.step}`);
          }
        })()}
        <SubmitQuestion {...this.state}/>
      </div>
    );
  }
}
