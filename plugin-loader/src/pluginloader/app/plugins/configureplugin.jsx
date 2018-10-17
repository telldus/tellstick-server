define(
	['react', 'react-mdl', 'react-redux', 'dialog-polyfill', 'telldus', 'plugins/actions', 'plugins/categoryicon'],
function(React, ReactMDL, ReactRedux, DialogPolyfill, Telldus, Actions, CategoryIcon ) {
	class ConfigBoolInput extends React.Component {
		render() {
			return (
				<ReactMDL.Checkbox
					label = {this.props.title}
					defaultChecked = {this.props.value}
					onChange = {e => this.props.onChange(e.target.checked)}
					ripple
				/>
			);
		}
	}
	class ConfigTextInput extends React.Component {
		constructor(props) {
			super(props)
			this.state = {
				value: this.props.value
			}
		}
		handleChange(e) {
			errorFlag = true;
			patternRegExp = new RegExp("^" + e.pattern + "$");
			if (!patternRegExp.test(e.value)) {
				errorFlag = false;
			}
			if (errorFlag) {
				this.setState({value: e.value});
				this.props.onChange(e.value)
			}
		}
		render() {
			if (this.props.maxLength != 0 || this.props.minLength != 0) {
				patternStr = ".{" + this.props.minLength + "," + this.props.maxLength + "}";
			} else {
				patternStr = ".{0,}";
			}
			return (
				<ReactMDL.Textfield
					floatingLabel
					onChange = {e => this.handleChange(e.target)}
					pattern = {patternStr}
					error = {this.props.title + " length must between " + this.props.minLength + " and " + this.props.maxLength + " characters"}
					label = {this.props.title}
					value = {this.state.value}
				/>
			);
		}
	}
	class ConfigNumberInput extends React.Component {
		constructor(props) {
			super(props)
			this.state = {
				value: this.props.value
			}
		}
		handleChange(e) {
			errorFlag = true;
			patternRegExp = new RegExp("^" + e.pattern + "$");
			if (!patternRegExp.test(e.value)) {
				errorFlag = false;
			}
			if (errorFlag) {
				this.setState({value: e.value});
				this.props.onChange(e.value)
			}
		}
		render() {
			if (this.props.maximum != 0 || this.props.minimum != 0) {
				patternStr = "[0-9]{" + this.props.minLength + "," + this.props.maxLength + "}";
				errorStr = "Please enter a number in the range " + this.props.minLength + " to " + this.props.maxLength;
			} else {
				patternStr = "[0-9]{0,}";
				errorStr = "Please enter a number."
			}
			return (
				<ReactMDL.Textfield
					floatingLabel
					pattern = {patternStr}
					error = {errorStr}
					onChange = {e => this.handleChange(e.target)}
					label = {this.props.title}
					value = {this.state.value}
				/>
			);
		}
	}
	class ConfigInput extends React.Component {
		render() {
			if (this.props.config.type == 'reactcomponent') {
				return (
					<Telldus.ComponentLoader
						name = {this.props.config.component}
						plugin = {this.props.plugin}
						pluginClass = {this.props.pluginClass}
						config = {this.props.name}
						{...this.props.config}
					/>
				)
			} else if (this.props.config.type == 'bool') {
				return <ConfigBoolInput onChange = {value => this.props.onChange(value)} {...this.props.config} />;
			} else if (this.props.config.type == 'number') {
				return <ConfigNumberInput onChange = {value => this.props.onChange(value)} {...this.props.config} />
			}
			// Default to a string
			return <ConfigTextInput onChange = {value => this.props.onChange(value)} {...this.props.config} />
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
				<ReactMDL.Dialog open = {this.props.show} ref = {(c) => this.dialog = c} style = {{width: 700, padding: '0'}}>
					<ReactMDL.DialogTitle>
						<CategoryIcon category = {this.props.plugin.category} color = {this.props.plugin.color} />
						Configure {this.props.plugin.name}</ReactMDL.DialogTitle>
					<ReactMDL.DialogContent>
						{Object.keys(this.props.plugin.config).map(name => (
							<div key = {name}>
								{Object.keys(this.props.plugin.config[name]).sort((a,b) => {
									let s1 = this.props.plugin.config[name][a].sortOrder;
									let s2 = this.props.plugin.config[name][b].sortOrder;
									return s1 - s2;
								}).map(config => (
									<div key = {config}>
										<ConfigInput
											plugin = {this.props.plugin.name}
											pluginClass = {name}
											name = {config}
											config = {this.props.plugin.config[name][config]}
											onChange = {v => this.handleChange(name, config, v)}
										/>
									</div>
								))}
							</div>
						))}
					</ReactMDL.DialogContent>
					<ReactMDL.DialogActions style = {{
						backgroundColor: this.props.plugin.color,
						padding: '12px'
					}}>
						<ReactMDL.Button type = 'button' className="buttonRounded buttonAccept" raised onClick={() => this.save()}>Save</ReactMDL.Button>
						<ReactMDL.Button type='button' className="buttonRounded buttonWhite" raised onClick={() => this.props.onClose()}>Close</ReactMDL.Button>
					</ReactMDL.DialogActions>
				</ReactMDL.Dialog>
			)
		}
	}

	ConfigurePlugin.propTypes = {
		plugin: React.PropTypes.object,
	};
	const mapStateToProps = (state) => ({
		plugin: state.plugins.find((plugin) => (plugin.name == state.configure)) || {name: '', config: {}, category: 'other', color: '#757575'},
		show: state.configure !== null,
	});
	const mapDispatchToProps = (dispatch) => ({
		onSave: (plugin, values) => dispatch(Actions.saveConfiguration(plugin, values)),
		onClose: () => dispatch(Actions.configurePlugin(null)),
	});
	return ReactRedux.connect(mapStateToProps, mapDispatchToProps)(ConfigurePlugin);
});
