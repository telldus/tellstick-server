import React from 'react';
import * as ReactMDL from 'react-mdl';
import * as ReactRedux from 'react-redux';
import * as Redux from 'redux';
import thunkMiddleware from 'redux-thunk';
import createLogger from 'redux-logger';
import dialogpolyfill from 'dialog-polyfill'

var requirejs = require('exports-loader?requirejs=requirejs&define!requirejs/require.js');

// Sorry, the scripts seems to needs this in the global context... :(
window.define = requirejs.define;

// Define some resources to requirejs modules
requirejs.define('react', [], React);
requirejs.define('react-mdl', [], ReactMDL);
requirejs.define('react-redux', [], ReactRedux);
requirejs.define('react-router', [], require('react-router'));
requirejs.define('css', require('./lib/css').default);
requirejs.define('dialog-polyfill', dialogpolyfill);
requirejs.define('telldus', require('./lib/telldus').default);
requirejs.define('websocket', require('./lib/websocket').default)

class Placeholder extends React.Component {
	render() {
		return (
			<div>Loading <ReactMDL.Spinner /></div>
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
		var packages = [];
		for(var i in this.props.plugins) {
			var path = this.props.plugins[i].script.slice(0, -3);  // Remove .js
			var index = path.lastIndexOf('/');
			packages.push({
				'name': this.props.plugins[i].name,
				'main': path.substr(index+1),
				'location': '/' + path.substr(0, index)
			})
		}
		var dynamicComponent = this;

		requirejs.requirejs.config({packages: packages});
		requirejs.requirejs([name], function(component) {
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
