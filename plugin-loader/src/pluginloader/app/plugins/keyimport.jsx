define(
	['react', 'react-mdl', 'react-redux', 'dialog-polyfill', 'plugins/actions', 'plugins/formatfingerprint'],
function(React, ReactMDL, ReactRedux, DialogPolyfill, Actions, formatFingerPrint ) {
	class KeyImport extends React.Component {
		componentDidMount() {
			if (!this.dialog.dialogRef.showModal) {
				DialogPolyfill.registerDialog(this.dialog.dialogRef);
			}
		}
		render() {
			return (
				<ReactMDL.Dialog open={this.props.show} ref={(c) => this.dialog = c} style={{width: 700}}>
					<ReactMDL.DialogTitle>You are about to install a plugin from an unverified developer</ReactMDL.DialogTitle>
					<ReactMDL.DialogContent>
						<p>Do you trust the developer {this.props.importkey.name}?</p>
						<p>Please make sure this fingerprint is the same as printed where you downloaded the plugin</p>
						<pre><p>{formatFingerPrint(this.props.importkey.fingerprint)}</p></pre>
					</ReactMDL.DialogContent>
					<ReactMDL.DialogActions>
						<ReactMDL.Button type='button' onClick={() => this.props.onAcceptKey(this.props.importkey.keyid)}>Yes</ReactMDL.Button>
						<ReactMDL.Button type='button' onClick={() => this.props.onDiscardKey()}>No</ReactMDL.Button>
					</ReactMDL.DialogActions>
				</ReactMDL.Dialog>
			)
		}
	}

	KeyImport.propTypes = {
		importkey: React.PropTypes.object,
		onAcceptKey: React.PropTypes.func,
		onDiscardKey: React.PropTypes.func,
	};
	const mapStateToProps = (state) => ({
		importkey: state.importingKey,
		show: state.importingKey.keyid !== null
	});
	const mapDispatchToProps = (dispatch) => ({
		onAcceptKey: (keyid) => dispatch(Actions.acceptKey(keyid)),
		onDiscardKey: () => dispatch(Actions.discardKey()),
	});
	return ReactRedux.connect(mapStateToProps, mapDispatchToProps)(KeyImport);
});
