define(
	['react', 'react-mdl', 'telldus', 'api/redux', 'api/methodslist', 'api/explorer'],
function(React, ReactMDL, Telldus, Redux, MethodsList, Explorer) {
	var store = Telldus.createStore(Redux.reducer);
	store.dispatch(Redux.fetchMethods());

	class APIApp extends React.Component {
		componentDidMount() {
			this.explore(this.props.location.query.explore);
		}
		componentWillReceiveProps(nextProps) {
			if (this.props.location.query.explore !== nextProps.location.query.explore) {
				this.explore(nextProps.location.query.explore);
			}
		}
		explore(method) {
			if (!method) {
				store.dispatch(Redux.closeExplorer());
				return;
			}
			let parts = method.split('/');
			store.dispatch(Redux.explore(parts[0], parts[1]));
		}
		render() {
			return (
				<div>
					<ReactMDL.Grid>
						<ReactMDL.Cell component={ReactMDL.Card} col={7} shadow={1}>
							<ReactMDL.CardTitle expand>Available methods</ReactMDL.CardTitle>
							<ReactMDL.CardText>
								<MethodsList store={store} />
							</ReactMDL.CardText>
						</ReactMDL.Cell>
					</ReactMDL.Grid>
					<Explorer store={store} />
				</div>
			)
		}
	};

	return APIApp;
});
