import React from 'react';
import ReactDOM from 'react-dom';
import { IndexRoute, Router, Route, browserHistory } from 'react-router'
import { createStore, applyMiddleware } from 'redux'
import { Provider } from 'react-redux';
import thunkMiddleware from 'redux-thunk'
import createLogger from 'redux-logger'

import App, {Index, About} from './components/App';
import Settings from './components/Settings';
import ComponentLoader from './components/ComponentLoader';
import {fetchComponents} from './actions/components'
import appReducers from './reducers/index'
import { componentsByTag } from './components/lib/telldus'

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
		return (<ComponentLoader store={store} name={this.props.route.name} {...this.props} />);
	}
}

class PageWrapper extends React.Component {
	render() {
		let Component = this.props.route.pageComponent;
		return (<Component store={store} />);
	}
}

store.dispatch(fetchComponents()).then(() => {
	let components = store.getState().components;
	let routes = Object.keys(components).reduce((a, b) => {
		if (components[b].path) {
			a.push(<Route path={components[b].path} key={b} name={b} component={ComponentWrapper} />);
		}
		return a;
	}, []);
	ReactDOM.render(
		<Router history={browserHistory}>
			<Route path="/" component={App} store={store}>
				<IndexRoute component={Index} />
				{routes}
				<Route path='/telldus/settings' component={PageWrapper} pageComponent={Settings} store={store} />
			</Route>
		</Router>,
		document.body.appendChild(document.createElement('div'))
	);
});
