define(
	['react', 'react-mdl', 'react-redux', 'dialog-polyfill', 'plugins/actions'],
function(React, ReactMDL, ReactRedux, DialogPolyfill, Actions) {
	class ErrorMEssage extends React.Component {
		componentDidMount() {
			if (!this.dialog.dialogRef.showModal) {
				DialogPolyfill.registerDialog(this.dialog.dialogRef);
			}
		}
		render() {
			return (
				<ReactMDL.Dialog open={this.props.show} ref={(c) => this.dialog = c} style={{width: 700}}>
					<ReactMDL.DialogTitle>Error importing plugin</ReactMDL.DialogTitle>
					<ReactMDL.DialogContent>
						<p>Plugin could not be imported:</p>
						<p>{this.props.msg}</p>
					</ReactMDL.DialogContent>
					<ReactMDL.DialogActions>
						<ReactMDL.Button type='button' onClick={() => this.props.onClose()}>Close</ReactMDL.Button>
					</ReactMDL.DialogActions>
				</ReactMDL.Dialog>
			)
		}
	}

	ErrorMEssage.propTypes = {
		msg: React.PropTypes.string,
		show: React.PropTypes.bool,
		onClose: React.PropTypes.func,
	};
	const mapStateToProps = (state) => ({
		msg: state.uploadErrorMsg,
		show: state.uploadErrorMsg != '',
	});
	const mapDispatchToProps = (dispatch) => ({
		onClose: () => dispatch(Actions.discardError()),
	});
	return ReactRedux.connect(mapStateToProps, mapDispatchToProps)(ErrorMEssage);
});
