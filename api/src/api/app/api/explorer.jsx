define(
	['react', 'react-mdl', 'react-router', 'react-redux', 'api/redux', 'dialog-polyfill'],
function(React, ReactMDL, ReactRouter, ReactRedux, Redux, DialogPolyfill ) {
	class ParameterInput extends React.Component {
		constructor(props) {
			super(props)
			this.state = {
				value: this.props.value
			}
		}
		handleChange(event) {
			this.setState({value: event.target.value});
			this.props.onChange(event.target.value)
		}
		render() {
			return (
				<ReactMDL.Textfield
					floatingLabel
					onChange={e => this.handleChange(e)}
					label={this.props.title}
					value={this.state.value}
				/>
			);
		}
	}
	ParameterInput.propTypes = {
		onChange: React.PropTypes.func,
	};

	class Explorer extends React.Component {
		componentDidMount() {
			if (!this.dialog.dialogRef.showModal) {
				DialogPolyfill.registerDialog(this.dialog.dialogRef);
			}
		}
		parameterChanged(parameter, value) {
			let state = {};
			state[parameter] = value;
			this.setState(state)
		}
		test() {
			this.props.onTest(this.props.module, this.props.action, this.state)
		}
		render() {
			return (
				<ReactMDL.Dialog open={this.props.show} ref={(c) => this.dialog = c} onCancel={() => ReactRouter.browserHistory.push('/api')} style={{width: 700}}>
					<ReactMDL.DialogTitle>{this.props.module}/{this.props.action}</ReactMDL.DialogTitle>
					<ReactMDL.DialogContent>
						<p>{this.props.func.doc.split("\n").map((item, i) => (
							<span key={i}>
								{item}
								<br />
							</span>
						))}</p>
						{this.props.func.args.map(item => (
							<div key={item}><ParameterInput title={item} value="" onChange={v => this.parameterChanged(item, v)} /></div>
						))}
						<ReactMDL.Button raised onClick={() => this.test()}>Test</ReactMDL.Button>
						<div>
							<pre>{JSON.stringify(this.props.result, null, 2)}</pre>
						</div>
					</ReactMDL.DialogContent>
					<ReactMDL.DialogActions>
						<ReactMDL.Button type='button' onClick={() => ReactRouter.browserHistory.push('/api')}>Close</ReactMDL.Button>
					</ReactMDL.DialogActions>
				</ReactMDL.Dialog>
			)
		}
	}

	Explorer.propTypes = {
		action: React.PropTypes.string,
		func: React.PropTypes.object,
		module: React.PropTypes.string,
		onTest: React.PropTypes.func,
		result: React.PropTypes.object,
		show: React.PropTypes.bool,
	};
	const mapStateToProps = (state) => ({
		action: state.explorer.action,
		func: state.methods[state.explorer.module] ? state.methods[state.explorer.module][state.explorer.action] : {doc: '', args: []},
		module: state.explorer.module,
		result: state.explorer.result,
		show: state.explorer.action != null,
	})
	const mapDispatchToProps = (dispatch) => ({
		onTest: (module, action, params) => dispatch(Redux.testMethod(module, action, params)),
	})
	return ReactRedux.connect(mapStateToProps, mapDispatchToProps)(Explorer);
});
