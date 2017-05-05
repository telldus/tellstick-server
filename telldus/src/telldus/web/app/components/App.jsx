import React from 'react';
import { Content, Drawer, Header, Layout, Navigation } from 'react-mdl';
import { IndexLink, Link } from 'react-router';
import { connect } from 'react-redux'

import 'react-mdl/extra/material.css';
import 'react-mdl/extra/material.js';
import 'dialog-polyfill/dialog-polyfill.css';
import '../fonts/telldusicons.css';

import Menu from './Menu'
import Logo from './Logo'

export class Index extends React.Component {
	render() {
		return <h1>Index</h1>
	}
}

export class About extends React.Component {
	render() {
		return <div>About</div>
	}
}

export default class App extends React.Component {
	render() {
		return (
			<Layout fixedDrawer style={{zIndex: 100001}}>
				<Drawer>
					<Logo />
					<Menu store={this.props.route.store} />
				</Drawer>
				<Content>
					{this.props.children}
				</Content>
			</Layout>
		);
	}
}
