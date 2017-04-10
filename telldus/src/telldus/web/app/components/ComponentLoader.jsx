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
requirejs.define('react-markdown', [], {Markdown: require('react-markdown')});
requirejs.define('css', require('./lib/css').default);
requirejs.define('dialog-polyfill', dialogpolyfill);
requirejs.define('telldus', require('./lib/telldus').default);
requirejs.define('websocket', require('./lib/websocket').default)

class Placeholder extends React.Component {
	render() {
		return (
			<div><ReactMDL.Spinner /></div>
		);
	}
};

class ComponentLoader extends React.Component {
	constructor(props) {
		super(props);
		this.state = {component: Placeholder}
	}

	componentDidMount() {
		this.loadComponent(this.props.name)
	}

	componentWillReceiveProps(nextProps) {
		if (this.props.name != nextProps.name) {
			// Changing page, load the new page
			this.loadComponent(nextProps.name);
		}
	}

	loadComponent(name) {
		var packages = [];
		for(var componentName in this.props.components) {
			var path = this.props.components[componentName].script.slice(0, -3);  // Remove .js
			var index = path.lastIndexOf('/');
			packages.push({
				'name': componentName,
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
			<PluginComponent location={this.props.location} {...this.props} />
		);
	}
};
ComponentLoader.propTypes = {
	name: React.PropTypes.string.isRequired,
}

const mapStateToProps = (state, ownProps) => {
	return {
		components: state.components
	}
}
export default ReactRedux.connect(mapStateToProps)(ComponentLoader)
