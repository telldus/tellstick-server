import {applyMiddleware, createStore, compose} from 'redux';
import thunkMiddleware from 'redux-thunk';
import createLogger from 'redux-logger';

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
			var requirejs = require('exports?requirejs=requirejs&define!requirejs/require.js');
			requirejs.requirejs(['css!' + file]);
		}
	};
};
