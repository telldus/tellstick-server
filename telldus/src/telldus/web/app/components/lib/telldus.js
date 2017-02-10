import {applyMiddleware, createStore, compose} from 'redux';
import thunkMiddleware from 'redux-thunk';
import createLogger from 'redux-logger';

export const componentsByTag = (components, tag) => (
	Object.keys(components).reduce((p, name) => {
		if (components[name].tags.indexOf(tag) >= 0) {
			p[name] = components[name];
		}
		return p;
	}, {})
);

export default function() {
	return {
		createStore: function(reducers) {
			return createStore(
				reducers,
				compose(
					applyMiddleware(
						thunkMiddleware
					),
					window.devToolsExtension ? window.devToolsExtension() : f => f
				)
			);
		},
		loadCSS: function(file) {
			var requirejs = require('exports-loader?requirejs=requirejs&define!requirejs/require.js');
			requirejs.requirejs(['css!' + file]);
		}
	};
};
