import React from 'react';
import ReactDOM from 'react-dom';
import { IndexRoute, Router, Route, hashHistory } from 'react-router'
import { createStore, applyMiddleware } from 'redux'
import { Provider } from 'react-redux';
import thunkMiddleware from 'redux-thunk'
import createLogger from 'redux-logger'

import App, {Index, About} from './components/App';
import PluginLoader from './components/PluginLoader';
import {fetchPlugins} from './actions/plugins'
import appReducers from './reducers/index'

const loggerMiddleware = createLogger()

var store = createStore(
	appReducers,
	applyMiddleware(
		thunkMiddleware
		//loggerMiddleware
	)
);

class ComponentWrapper extends React.Component {
	render() {
		return (<PluginLoader store={store} {...this.props.params} />);
	}
}

store.dispatch(fetchPlugins()).then(() => {
	ReactDOM.render(
		<Router history={hashHistory}>
			<Route path="/" component={App} store={store}>
				<IndexRoute component={Index} />
				<Route path="/plugin/:name" component={ComponentWrapper} />
			</Route>
		</Router>,
		document.body.appendChild(document.createElement('div'))
	);
});
