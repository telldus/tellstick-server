define(
	['react', 'react-mdl', 'react-redux', 'dialog-polyfill', 'telldus', 'plugins/actions'],
function(React, ReactMDL, ReactRedux, DialogPolyfill, Telldus, Actions ) {
	class ConfigTextInput extends React.Component {
		constructor(props) {
			super(props)
			this.state = {
				value: this.props.value
			}
		}
		handleChange(value) {
			this.setState({value: value});
			this.props.onChange(value)
		}
		render() {
			return (
				<ReactMDL.Textfield
					floatingLabel
					onChange={e => this.handleChange(e.target.value)}
					label={this.props.title}
					value={this.state.value}
				/>
			);

		}
	}
	class ConfigInput extends React.Component {
		render() {
			if (this.props.type == 'reactcomponent') {
				return <Telldus.ComponentLoader name={this.props.component} />
			}
			// Default to a string
			return <ConfigTextInput onChange={value => this.onChange(value)} {...this.props} />
		}
	}
	ConfigInput.propTypes = {
		onChange: React.PropTypes.func,
	};

	class ConfigurePlugin extends React.Component {
		constructor(props) {
			super(props);
			this.state = {
				values: {}
			}
		}
		componentDidMount() {
			if (!this.dialog.dialogRef.showModal) {
				DialogPolyfill.registerDialog(this.dialog.dialogRef);
			}
		}
		handleChange(name, config, value) {
			let state = {};
			let values = {...this.state.values[name]};
			values[config] = value
			state[name] = values;
			this.setState({values: state})
		}
		save() {
			this.props.onSave(this.props.plugin.name, this.state.values)
		}
		render() {
			return (
				<ReactMDL.Dialog open={this.props.show} ref={(c) => this.dialog = c} style={{width: 700}}>
					<ReactMDL.DialogTitle>Configure {this.props.plugin.name}</ReactMDL.DialogTitle>
					<ReactMDL.DialogContent>
						{Object.keys(this.props.plugin.config).map(name => (
							<div key={name}>
								{Object.keys(this.props.plugin.config[name]).map(config => (
									<div key={config}>
										<ConfigInput
											{...this.props.plugin.config[name][config]}
											onChange={v => this.handleChange(name, config, v)}
										/>
									</div>
								))}
							</div>
						))}
					</ReactMDL.DialogContent>
					<ReactMDL.DialogActions>
						<ReactMDL.Button type='button' onClick={() => this.save()}>Save</ReactMDL.Button>
						<ReactMDL.Button type='button' onClick={() => this.props.onClose()}>Close</ReactMDL.Button>
					</ReactMDL.DialogActions>
				</ReactMDL.Dialog>
			)
		}
	}

	ConfigurePlugin.propTypes = {
		plugin: React.PropTypes.object,
	};
	const mapStateToProps = (state) => ({
		plugin: state.plugins.find((plugin) => (plugin.name == state.configure)) || {name: '', config: {}},
		show: state.configure !== null
	});
	const mapDispatchToProps = (dispatch) => ({
		onSave: (plugin, values) => dispatch(Actions.saveConfiguration(plugin, values)),
		onClose: () => dispatch(Actions.configurePlugin(null)),
	});
	return ReactRedux.connect(mapStateToProps, mapDispatchToProps)(ConfigurePlugin);
});
