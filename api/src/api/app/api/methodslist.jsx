define(
	['react', 'react-mdl', 'react-router', 'react-redux', 'api/redux'],
function(React, ReactMDL, ReactRouter, ReactRedux, Redux ) {
	class MethodsList extends React.Component {
		render() {
			return (
				<div>
					{Object.keys(this.props.methods).map(module =>
						<div key={module}>
							<h5>{module}</h5>
							<ReactMDL.List>
							{Object.keys(this.props.methods[module]).map(action =>
									<ReactMDL.ListItem key={action} twoLine>
										<ReactMDL.ListItemContent subtitle={this.props.methods[module][action].doc}>{action}</ReactMDL.ListItemContent>
										<ReactMDL.ListItemAction info="test">
											<ReactRouter.Link to={{ pathname: '/api', query: { explore: `${module}/${action}` } }}><ReactMDL.Icon name="explore" /></ReactRouter.Link>
										</ReactMDL.ListItemAction>
									</ReactMDL.ListItem>
							)}
							</ReactMDL.List>
						</div>
					)}
				</div>
			)
		}
	}

	MethodsList.propTypes = {
		methods: React.PropTypes.object,
	};
	const mapStateToProps = (state) => ({
		methods: state.methods,
	})
	return ReactRedux.connect(mapStateToProps)(MethodsList);
});
