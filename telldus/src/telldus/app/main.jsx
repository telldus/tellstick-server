import React from 'react';
import ReactDOM from 'react-dom';
import { IndexRoute, Router, Route, browserHistory } from 'react-router'
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
		return (<PluginLoader store={store} {...this.props.route.plugin} />);
	}
}

store.dispatch(fetchPlugins()).then(() => {
	var routes = store.getState().plugins.map(function(plugin) {
		return (
			<Route path={`${plugin.path}`} key={plugin.name} plugin={plugin} component={ComponentWrapper} />
		);
	});
	ReactDOM.render(
		<Router history={browserHistory}>
			<Route path="/" component={App} store={store}>
				<IndexRoute component={Index} />
				{routes}
			</Route>
		</Router>,
		document.body.appendChild(document.createElement('div'))
	);
});
