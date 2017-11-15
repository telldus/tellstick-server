import React from 'react';
import { connect } from 'react-redux';
import { Button, CardActions, CardText } from 'react-mdl';

class Firmware extends React.Component {
	updateDistribution(name) {
		// TODO
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
});
export const FirmwareSettings = connect(mapStateToProps, mapDispatchToProps)(Firmware)
