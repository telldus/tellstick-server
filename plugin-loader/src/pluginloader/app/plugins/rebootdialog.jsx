define(
	['react', 'react-mdl', 'react-redux', 'dialog-polyfill', 'plugins/actions', 'plugins/categoryicon'],
function(React, ReactMDL, ReactRedux, DialogPolyfill, Actions, CategoryIcon ) {
	class RebootDialog extends React.Component {
		constructor(props) {
			super(props);
		}
		componentDidMount() {
			if (!this.dialog.dialogRef.showModal) {
				DialogPolyfill.registerDialog(this.dialog.dialogRef);
			}
		}
		render() {
			return (
				<ReactMDL.Dialog style={{
					width: '400px',
					padding: '0'
				}} open={this.props.open} ref={c => {this.dialog = c}}>
					<ReactMDL.DialogTitle style={{
						color: '#555'
					}}>
						<CategoryIcon category="restart" color="#757575" />
						{this.props.requireReboot && <span>Reboot required</span>}
						{!this.props.requireReboot && <span>Reboot TellStick</span>}
					</ReactMDL.DialogTitle>
					<ReactMDL.DialogContent>
						{this.props.requireReboot &&
							<p>Your TellStick need to be rebooted before the changes will take effect.</p>
						}
						<p>Rebooting will take about 5 minutes.</p>
						<div style={{color: 'red', display: this.props.rebootStatus == -1 ? '' : 'none'}}>Error. Could not reboot device.</div>
					</ReactMDL.DialogContent>
					<ReactMDL.DialogActions style={{
						backgroundColor: '#757575',
						padding: '12px'
					}}>
						<ReactMDL.Button className="buttonRounded buttonWhite" onClick={() => this.props.onClose()} raised>Close</ReactMDL.Button>
						<ReactMDL.Button raised className="buttonRounded buttonAccept" disabled={this.props.rebootStatus > 0} onClick={() => this.props.onReboot()} style={{
							backgroundColor: '#9ccc65'
						}}>Reboot</ReactMDL.Button>
						<ReactMDL.Spinner style={{display: (this.props.rebootStatus == 1 ? '' : 'none')}}/>
					</ReactMDL.DialogActions>
				</ReactMDL.Dialog>
			)
		}
	}

	RebootDialog.propTypes = {
	};
	const mapStateToProps = (state) => ({
		open: state.showRebootDialog,
		rebootStatus: state.rebootStatus,
		requireReboot: state.requireReboot,
	});
	const mapDispatchToProps = (dispatch) => ({
		onClose: () => dispatch(Actions.showRebootDialog(false)),
		onReboot: () => dispatch(Actions.reboot()),
	});
	return ReactRedux.connect(mapStateToProps, mapDispatchToProps)(RebootDialog);
});
