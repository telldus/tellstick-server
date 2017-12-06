import React from 'react';
import { Card, CardTitle, Cell, Grid } from 'react-mdl';
import { connect } from 'react-redux';
import { componentsByTag } from './lib/telldus'
import { fetchTelldusInfo } from '../actions/settings'

import ComponentLoader from './ComponentLoader'

class Def extends React.Component {
	render() {
		return <div>Def</div>
	}
}

class SettingsCard extends React.Component {
	render() {
		let props = {};
		if (this.props.builtin) {
			props['store'] = this.props.store;
		}
		return (
			<Card className={this.props.className}>
				<CardTitle className="mdl-card__title mdl-color--primary mdl-color-text--white">{this.props.title}</CardTitle>
				<ComponentLoader name={this.props.name} {...props} />
			</Card>
		)
	}
}

class Settings extends React.Component {
	componentDidMount() {
		if (this.props.needsRefresh) {
			this.props.onRefresh();
		}
	}
	render() {
		return (
			<Grid>
				{Object.keys(this.props.components).map(name => (
					<Cell
						col={4}
						component={SettingsCard}
						shadow={1}
						key={name}
						store={this.props.store}
						name={name}
						{...this.props.components[name]}
					/>
				))}
			</Grid>
		);
	}
}

const mapStateToProps = (state) => {
  return {
		needsRefresh: !state.settings.updated,
		components: componentsByTag(state.components, 'settings'),
  }
}
const mapDispatchToProps = (dispatch) => ({
	onRefresh: () => dispatch(fetchTelldusInfo()),
});
export default connect(mapStateToProps, mapDispatchToProps)(Settings)
