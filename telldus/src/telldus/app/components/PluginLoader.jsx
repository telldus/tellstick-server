import React from 'react';
import * as ReactMDL from 'react-mdl';
import * as ReactRedux from 'react-redux';
import * as ReactRouter from 'react-router'
import * as Redux from 'redux';
import thunkMiddleware from 'redux-thunk';
import createLogger from 'redux-logger';
import dialogpolyfill from 'dialog-polyfill'

var requirejs = require('exports?requirejs=requirejs&define!requirejs/require.js');
requirejs.requirejs.config({
	jsx: {
		fileExtension: '.jsx'
	},
	baseUrl: '/',
	paths: {
		'jsx': '/telldus/js/jsx',
		'JSXTransformer': '/telldus/js/JSXTransformer',
		'text': '/telldus/js/text'
	}
});
// Sorry, the scripts seems to needs this in the global context... :(
window.define = requirejs.define;

// Define some resources to requirejs modules
requirejs.define('react', [], React);
requirejs.define('react-mdl', [], ReactMDL);
requirejs.define('react-redux', [], ReactRedux);
requirejs.define('react-router', [], ReactRouter);
requirejs.define('css', function () {
	return {
		load: function (name, parentRequire, onload, config) {
			var link = document.createElement("link");
			link.type = "text/css";
			link.rel = "stylesheet";
			link.href = name;
			document.getElementsByTagName("head")[0].appendChild(link);
			onload(null);
		}
	}
});
requirejs.define('telldus', function () {
	return {
		createStore: function(reducers) {
			return Redux.createStore(
				reducers,
				Redux.compose(
					Redux.applyMiddleware(
						thunkMiddleware
					),
					window.devToolsExtension ? window.devToolsExtension() : f => f
				)
			);
		}
	};
});
requirejs.define('dialog-polyfill', dialogpolyfill);
requirejs.define('websocket', function() {
	var onMessage = [];

	var WebSocketWrapper = function() {
		console.log("Create new websocket main object");
		this.setup();
	}

	WebSocketWrapper.prototype.setup = function() {
		this.ws = new WebSocket('ws://' + location.host + '/ws');
		this.ws.onopen = function() {
			console.log("Websocket opened");
		};

		this.ws.onmessage = function (evt) {
			var obj = JSON.parse( evt.data );
			for(var i = 0; i < onMessage.length; ++i) {
				onMessage[i].messageReceived(obj['module'], obj['action'], obj['data']);
			}
		};

		this.ws.onclose = function() {
			// websocket is closed.
			console.log("Websocket closed");
		};
	}

	WebSocketWrapper.prototype.register = function (evt) {
		onMessage.push(evt);
	};

	WebSocketWrapper.prototype.unregister = function (evt) {
		var index = onMessage.indexOf(evt)
		if (index >= 0) {
			onMessage.splice(index, 1);
		}
	};

	var ws = new WebSocketWrapper();

	var WebSocketInstance = function() {
		this.filter = [];
	}

	WebSocketInstance.prototype.messageReceived = function(module, action, data) {
		for(var i = 0; i < this.filter.length; ++i) {
			if (this.filter[i].module === module && this.filter[i].action === action) {
				this.filter[i].fn(module, action, data);
			}
		}
	}

	WebSocketInstance.prototype.onMessage = function (module, action, evt) {
		if (evt == null) {
			for(var i = 0; i < this.filter.length; ++i) {
				if (this.filter[i].module === module && this.filter[i].action === action) {
					this.filter.splice(i, 1);
					break;
				}
			}
			if (this.filter.length == 0) {
				ws.unregister(this);
			}
		} else {
			if (this.filter.length == 0) {
				ws.register(this);
			}
			this.filter.push({module: module, action: action, fn: evt});
		}
	};

	return WebSocketInstance;
})

class Placeholder extends React.Component {
	render() {
		return (
			<div>Placeholder</div>
		);
	}
};

class PluginLoader extends React.Component {
	constructor(props) {
		super(props);
		this.state = {component: Placeholder}
	}

	componentDidMount() {
		this.loadPluginComponent(this.props.name)
	}

	componentWillReceiveProps(nextProps) {
		if (this.props.params.name != nextProps.name) {
			// Changing page, load the new page
			this.loadPluginComponent(nextProps.name);
		}
	}

	loadPluginComponent(name) {
		var script = null;
		for(var i in this.props.plugins) {
			if (this.props.plugins[i].name == name) {
				script = this.props.plugins[i].script;
			}
		}
		if (!script) {
			return;
		}
		var dynamicComponent = this;
		var url = (script.substr(-4) === '.jsx' ? 'jsx!' + script.slice(0, - 4) : script)
		requirejs.requirejs([url], function(component) {
			//console.log("Comp", component);
			dynamicComponent.setState({component: component});
		});
	}

	render() {
		var PluginComponent = this.state.component;
		return (
			<div>
				<PluginComponent location={this.props.location} />
			</div>
		);
	}
};

const mapStateToProps = (state, ownProps) => {
	return {
		plugins: state.plugins
	}
}
export default ReactRedux.connect(mapStateToProps)(PluginLoader)
