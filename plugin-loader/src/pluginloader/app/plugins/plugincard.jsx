define(
	['react', 'react-mdl', 'react-redux', 'plugins/actions'],
function(React, ReactMDL, ReactRedux, Actions ) {
	class PluginCard extends React.Component {
		render() {
			return (
				<ReactMDL.Card className={this.props.className}>
					<ReactMDL.CardTitle style={{
						color: '#fff',
						backgroundColor: this.props.color ? this.props.color : PluginCard.defaultProps.color
					}}>
						{this.props.name}
					</ReactMDL.CardTitle>
					<ReactMDL.CardText style={{
						height: '96px',
						background: 'url(' + this.props.icon + ') center no-repeat',
						textAlign: 'center',
					}}>
						{!this.props.icon && <ReactMDL.Icon name="extension" style={{fontSize: '96px', lineHeight: '96px'}} />}
					</ReactMDL.CardText>
					<ReactMDL.CardText style={{
						whiteSpace: 'nowrap',
						textOverflow: 'ellipsis',
						height: '25px'
					}}>
						{this.props.description}
					</ReactMDL.CardText>
					<ReactMDL.CardActions border>
						<ReactMDL.Button onClick={() => this.props.onMoreInfo()}>More info</ReactMDL.Button>
					</ReactMDL.CardActions>
					<ReactMDL.CardMenu>
						{this.props.showSettings && <ReactMDL.IconButton name="settings" style={{color: '#fff'}} onClick={() => this.props.onSettingsClicked()}/>}
					</ReactMDL.CardMenu>
				</ReactMDL.Card>
			)
		}
	}
	PluginCard.propTypes = {
		description: React.PropTypes.string.isRequired,
		icon: React.PropTypes.string.isRequired,
		installed: React.PropTypes.bool.isRequired,
		name: React.PropTypes.string.isRequired,
		onSettingsClicked:React.PropTypes.func,
		onMoreInfo: React.PropTypes.func,
	};
	PluginCard.defaultProps = {
		color: '#757575',
		onMoreInfo: () => {}
	};
	return PluginCard;
});
