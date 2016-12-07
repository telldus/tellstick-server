import React from 'react';
import { Navigation } from 'react-mdl';
import { IndexLink, Link } from 'react-router';
import { connect, Provider } from 'react-redux'

class Menu extends React.Component {
	constructor(props) {
		super(props);
	}

	render() {
		let nodes = this.props.plugins.reduce( (a, b) => (
			b.title ? a.concat(b) : a
		), []).map(plugin => (
			<Link to={`${plugin.path}`} activeClassName="is-active" key={plugin.name}>{plugin.title}</Link>
		));
		return (
			<Provider store={this.props.store}>
				<Navigation>
					<IndexLink to="/" activeClassName="is-active">Index</IndexLink>
					{nodes}
				</Navigation>
			</Provider>
		);
	}
};

const mapStateToProps = (state, ownProps) => {
	return {
		plugins: state.plugins
	}
}
export default connect(mapStateToProps)(Menu);
