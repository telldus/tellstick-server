import React from 'react';
import { connect } from 'react-redux';
import { Button, CardActions, CardText, Dialog, DialogActions, DialogContent, DialogTitle, Spinner } from 'react-mdl';

import { setDistribution } from '../actions/settings'

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
			<Dialog style={{
				width: '500px',
				padding: '0'
			}} open={this.props.open} ref={c => {this.dialog = c}}>
				<DialogTitle style={{
					color: '#555'
				}}>
					<span>Confirm change to {this.props.distribution}</span>
				</DialogTitle>
				<DialogContent>
					<p>Your TellStick needs to be rebooted before the changes will take effect.</p>
					<p>Rebooting will take about 10 minutes or more.</p>
					<p>Do not disconnect the power to your TellStick while upgrading. This may break your TellStick</p>
					<p>Your TellStick will not be accessible during the upgrade</p>
					<div style={{color: 'red', display: this.props.rebootStatus == -1 ? '' : 'none'}}>Error. Could not reboot device.</div>
				</DialogContent>
				<DialogActions style={{
					backgroundColor: '#757575',
					padding: '12px'
				}}>
					<Button className="buttonRounded buttonWhite" onClick={() => this.props.onClose()} raised>Abort</Button>
					<Button raised className="buttonRounded buttonAccept" disabled={this.props.rebootStatus > 0} onClick={() => this.props.onReboot()} style={{
						backgroundColor: '#9ccc65'
					}}>Reboot now</Button>
					<Spinner style={{display: (this.props.rebootStatus == 1 ? '' : 'none')}}/>
				</DialogActions>
			</Dialog>
		)
	}
}

class Firmware extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			'rebootShown': false,
			'rebootStatus': 0,
			'distribution': '',
		}
	}
	updateDistribution(name) {
		this.setState({
			'rebootShown': true,
			'rebootStatus': 0,
			'distribution': name,
		});
	}
	setAndReboot() {
		this.setState({
			'rebootStatus': 1
		});
		this.props.onSetDistribution(this.state.distribution);
	}
	render() {
		return (
			<div>
				<CardText>
					Your TellStick is currently running {this.props.distribution} version {this.props.version}
				</CardText>
				<CardActions border>
					{this.props.distribution != 'beta' && <Button onClick={() => this.updateDistribution('beta')} colored>Switch to beta</Button>}
					{this.props.distribution != 'stable' && <Button onClick={() => this.updateDistribution('stable')} colored>Switch to stable</Button>}
				</CardActions>
				<RebootDialog
					open={this.state.rebootShown}
					distribution={this.state.distribution}
					rebootStatus={this.state.rebootStatus}
					onClose={() => this.setState({'rebootShown': false})}
					onReboot={() => this.setAndReboot()}
				/>
			</div>
		)
	}
}
const mapStateToProps = (state) => {
  return {
		'distribution': state.settings.firmware.distribution,
		'version': state.settings.firmware.version,
  }
}
const mapDispatchToProps = (dispatch) => ({
	onSetDistribution: (name) => dispatch(setDistribution(name)),
});
export const FirmwareSettings = connect(mapStateToProps, mapDispatchToProps)(Firmware)
