define(
	['react', 'react-mdl', 'react-redux', 'plugins/actions', 'plugins/categoryicon'],
function(React, ReactMDL, ReactRedux, Actions, CategoryIcon ) {
	class PluginCard extends React.Component {
		render() {
			return (

				<ReactMDL.Card className={this.props.className}>
					<ReactMDL.CardTitle style={{
						padding: '16px 16px 0 16px'
					}}>
						<CategoryIcon category={this.props.category} color={this.props.color} />
					</ReactMDL.CardTitle>
					<ReactMDL.CardText style={{
						height: '96px',
						background: 'url(' + this.props.icon + ') center no-repeat',
						textAlign: 'center',
						padding: '0 16px'
					}}>
						{!this.props.icon && <ReactMDL.Icon name="extension" style={{fontSize: '96px', lineHeight: '96px'}} />}
					</ReactMDL.CardText>

					<ReactMDL.CardText style={{
						textAlign: 'center',
						fontSize: '18px',
						whiteSpace: 'nowrap',
						textOverflow: 'ellipsis',
						padding: '16px 16px 0 16px'
					}}>
						{this.props.name}
					</ReactMDL.CardText>


					<ReactMDL.CardText style={{
						textAlign: 'center',
						whiteSpace: 'nowrap',
						textOverflow: 'ellipsis',
						height: '25px'
					}}>
						{this.props.description}
					</ReactMDL.CardText>
					<ReactMDL.CardActions style={{
						color: this.props.color ? this.props.color : PluginCard.defaultProps.color,
						backgroundColor: this.props.color ? this.props.color : PluginCard.defaultProps.color
					}}>
						<ReactMDL.Button className='buttonWhiteBorder' onClick={() => this.props.onMoreInfo()}>More info</ReactMDL.Button>
					</ReactMDL.CardActions>
					<ReactMDL.CardMenu>
						<ReactMDL.Tooltip label="Upgrade plugin" position="left">
						<ReactMDL.IconButton name="arrow_upward" style={{color: '#fff', backgroundColor: '#9ccc65'}} onClick={() => this.props.onMoreInfo()} />
						</ReactMDL.Tooltip>
						{this.props.showSettings && <ReactMDL.IconButton name="settings" style={{color: '#aaa', marginLeft: '5px'}} onClick={() => this.props.onSettingsClicked()}/>}
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
