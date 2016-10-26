define(
	['react', 'react-mdl', 'react-redux', 'plugins/actions'],
function(React, ReactMDL, ReactRedux, Actions ) {
	class PluginsList extends React.Component {
		render() {
			return (
				<ReactMDL.List>
					{this.props.plugins.map(plugin =>
						<ReactMDL.ListItem key={plugin.name} twoLine>
							<ReactMDL.ListItemContent>{plugin.name}</ReactMDL.ListItemContent>
							<ReactMDL.ListItemAction>
								<a onClick={() => this.props.onRemovePlugin(plugin.name)}><ReactMDL.Icon name="delete" /></a>
							</ReactMDL.ListItemAction>
						</ReactMDL.ListItem>
					)}
				</ReactMDL.List>
			)
		}
	}

	PluginsList.propTypes = {
		plugins: React.PropTypes.array,
		onRemovePlugin: React.PropTypes.func,
	};
	const mapStateToProps = (state) => ({
		plugins: state.plugins,
	})
	const mapDispatchToProps = (dispatch) => ({
		onRemovePlugin: (name) => dispatch(Actions.deletePlugin(name))
	})
	return ReactRedux.connect(mapStateToProps, mapDispatchToProps)(PluginsList);
});
