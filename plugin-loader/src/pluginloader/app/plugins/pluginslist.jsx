define(
	['react', 'react-mdl', 'react-redux', 'plugins/actions', 'plugins/plugincard'],
function(React, ReactMDL, ReactRedux, Actions, PluginCard ) {
	class PluginsList extends React.Component {
		render() {
			return (
				<ReactMDL.Grid>
					{this.props.plugins.map(plugin =>
						<ReactMDL.Cell
							component={PluginCard}
							col={3}
							shadow={1}
							key={plugin.name}
							{...plugin}
							installed={true}
							onMoreInfo={() => this.props.onMoreInfo(plugin.name)}
							onSettingsClicked={() => this.props.onConfigurePlugin(plugin.name)}
							showSettings={Object.keys(plugin.config).length > 0}
						/>
					)}
				</ReactMDL.Grid>
			);
		}
	}

	PluginsList.propTypes = {
		plugins: React.PropTypes.array,
		onConfigurePlugin: React.PropTypes.func,
		onMoreInfo: React.PropTypes.func,
		onRemovePlugin: React.PropTypes.func,
	};
	const mapStateToProps = (state) => ({
		plugins: state.plugins,
	})
	const mapDispatchToProps = (dispatch) => ({
		onConfigurePlugin: (plugin) => dispatch(Actions.configurePlugin(plugin)),
		onMoreInfo: (plugin) => dispatch(Actions.showPluginInfo(plugin)),
		onRemovePlugin: (name) => dispatch(Actions.deletePlugin(name)),
	})
	return ReactRedux.connect(mapStateToProps, mapDispatchToProps)(PluginsList);
});
