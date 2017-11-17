import React from 'react';
import { Content, Drawer, Header, Layout, Navigation, Card, CardTitle, CardText, CardActions, Button, Grid, Cell } from 'react-mdl';
import { IndexLink, Link } from 'react-router';
import { connect } from 'react-redux'

import 'react-mdl/extra/material.css';
import 'react-mdl/extra/material.js';
import 'dialog-polyfill/dialog-polyfill.css';
import '../fonts/telldusicons.css';
import '../css/telldus.css';

import Menu from './Menu'
import Logo from './Logo'

export class Index extends React.Component {
	render() {
		return (
			<div>
				<h1>Index</h1>

				<Grid>
					<Cell col={3}>
						<Card shadow={1} style={{
							minHeight: '100px',
							width: 'auto'
						}}>
							<CardTitle style={{
								padding: '16px 16px 0 16px'
							}}>
								<div className='iconContainer'>
								<i className="telldus-icons" style={{
									fontSize: '24px'
								}}>device-alt-solid</i>
								</div>
							</CardTitle>
							<CardText className='nodeName'>
								Livingroom Lights
							</CardText>
							<CardActions style={{
								color: '#e26901',
								backgroundColor: '#e26901'
							}}>
								<Button className='buttonWhiteBorder'>Upgrade</Button>
							</CardActions>
						</Card>
					</Cell>


					<Cell col={3}>
						<Card shadow={1} style={{
							minHeight: '100px',
							width: 'auto'
						}}>
							<CardTitle style={{
								padding: '16px 16px 0 16px'
							}}>
								<div className='iconContainer'>
								<i className="telldus-icons" style={{
									fontSize: '24px'
								}}>sensor</i>
								</div>
							</CardTitle>
							<CardText className='nodeName'>
								Outdoor Temp.
							</CardText>
							<CardActions style={{
								color: '#e26901',
								backgroundColor: '#e26901',
							}}>
								<i style={{color: '#fff', lineHeight: '36px', height: '36px', fontSize: '14px' }}>This node cannot be upgraded</i>
							</CardActions>
						</Card>
					</Cell>

				</Grid>

			</div>
		);
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
