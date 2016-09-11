import React from 'react';
import * as ReactMDL from 'react-mdl';
import { connect } from 'react-redux'

var requirejs = require('exports?requirejs=requirejs&define!requirejs/require.js');
requirejs.requirejs.config({
	jsx: {
		fileExtension: '.jsx'
	},
	baseUrl: '/',
	paths: {
		'jsx': '/web/js/jsx',
		'JSXTransformer': '/web/js/JSXTransformer',
		'text': '/web/js/text'
	}
});
// Sorry, the scripts seems to needs this in the global context... :(
window.define = requirejs.define;

// Define some resources to requirejs modules
requirejs.define('react', [], React);
requirejs.define('react-mdl', [], ReactMDL);

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
		this.loadPluginComponent(this.props.params.name)
	}

	componentWillReceiveProps(nextProps) {
		if (this.props.params.name != nextProps.params.name) {
			// Changing page, load the new page
			this.loadPluginComponent(nextProps.params.name);
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
				<span>Dynamic component {this.props.params.name}</span>
				<PluginComponent />
			</div>
		);
	}
};

const mapStateToProps = (state, ownProps) => {
	return {
		plugins: state.plugins
	}
}
export default connect(mapStateToProps)(PluginLoader)
