import React from 'react';
import { Navigation } from 'react-mdl';
import { IndexLink, Link } from 'react-router';
import { connect, Provider } from 'react-redux'
import { componentsByTag } from './lib/telldus'

class Menu extends React.Component {
	constructor(props) {
		super(props);
	}

	render() {
		return (
			<Provider store={this.props.store}>
				<Navigation>
					<IndexLink to="/" activeClassName="is-active">Index</IndexLink>
					{Object.keys(this.props.components).map(name => (
						<Link to={`${this.props.components[name].path}`} activeClassName="is-active" key={name}>{this.props.components[name].title}</Link>
					))}
				</Navigation>
			</Provider>
		);
	}
};

const mapStateToProps = (state, ownProps) => {
	return {
		components: componentsByTag(state.components, 'menu'),
	}
}
export default connect(mapStateToProps)(Menu);
