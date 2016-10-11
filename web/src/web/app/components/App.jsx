import React from 'react';
import { Content, Drawer, Header, Layout, Navigation } from 'react-mdl';
import { IndexLink, Link } from 'react-router';
import { connect } from 'react-redux'

import 'react-mdl/extra/material.css';
import 'react-mdl/extra/material.js';
import 'dialog-polyfill/dialog-polyfill.css';

import Menu from './Menu'

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
			<Layout fixedDrawer fixedHeader style={{zIndex: 100001}}>
				<Header transparent title="TellStick Local Access" style={{background: '#1b365d'}}>
				</Header>
				<Drawer title="Main Menu">
					<Menu />
				</Drawer>
				<Content>
					{this.props.children}
				</Content>
			</Layout>
		);
	}
}
