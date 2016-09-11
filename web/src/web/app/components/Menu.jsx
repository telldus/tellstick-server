import React from 'react';
import { Navigation } from 'react-mdl';
import { IndexLink, Link } from 'react-router';
import { connect } from 'react-redux'

class Menu extends React.Component {
	constructor(props) {
		super(props);
	}

	render() {
		var nodes = this.props.plugins.map(function(plugin) {
			return (
				<Link to={`/plugin/${plugin.name}`} activeClassName="is-active" key={plugin.name}>{plugin.title}</Link>
			);
		});
		return (
			<Navigation>
				<IndexLink to="/" activeClassName="is-active">Index</IndexLink>
				{nodes}
				<Link to="/about" activeClassName="is-active">About</Link>
				<Link to="/mark" activeClassName="is-active">Mark</Link>
			</Navigation>
		);
	}
};

const mapStateToProps = (state, ownProps) => {
	return {
		plugins: state.plugins
	}
}
export default connect(mapStateToProps)(Menu);
