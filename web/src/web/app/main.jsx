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
		thunkMiddleware,
		loggerMiddleware
	)
);

store.dispatch(fetchPlugins()).then(() => {
	ReactDOM.render(
		<Provider store={store}>
			<Router history={hashHistory}>
				<Route path="/" component={App}>
					<IndexRoute component={Index} />
					<Route path="/plugin/:name" component={PluginLoader}/>
					<Route path="/about" component={About}/>
				</Route>
			</Router>
		</Provider>,
		document.body.appendChild(document.createElement('div'))
	);
});
