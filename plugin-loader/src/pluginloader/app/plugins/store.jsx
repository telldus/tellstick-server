define(
	['react', 'react-mdl', 'react-redux', 'plugins/actions', 'plugins/plugincard'],
function(React, ReactMDL, ReactRedux, Actions, PluginCard ) {
	class Store extends React.Component {
		render() {
			let style = {

			}
			return (
				<ReactMDL.Grid>
					{this.props.plugins.map(plugin =>
						<ReactMDL.Cell
							component={PluginCard}
							col={3}
							shadow={1}
							key={plugin.name}
							{...plugin}
							installed={false}
							onMoreInfo={() => this.props.onMoreInfo(plugin.name)}
						/>
					)}
				</ReactMDL.Grid>
			)
		}
	}

	Store.propTypes = {
		plugins: React.PropTypes.array,
		onMoreInfo: React.PropTypes.func,
		//onRemovePlugin: React.PropTypes.func,
	};
	const mapStateToProps = (state) => ({
		plugins: state.storePlugins.reduce((a, b) => {
			// Reduce installed plugins
			if (state.plugins.find(p => (p.name == b.name))) {
				return a;
			}
			// Reduce on search filter
			if (state.search != '' && b.name, b.name.toLowerCase().indexOf(state.search.toLowerCase()) == -1) {
				return a;
			}
			return a.concat(b)
		}, [])
	})
	const mapDispatchToProps = (dispatch) => ({
		onMoreInfo: (plugin) => dispatch(Actions.showPluginInfo(plugin)),
		//onRemovePlugin: (name) => dispatch(Actions.deletePlugin(name)),
	})
	return ReactRedux.connect(mapStateToProps, mapDispatchToProps)(Store);
});
