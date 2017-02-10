import React from 'react';

export default class App extends React.Component {
	componentDidMount() {
		setInterval(() => { this.renderClock()}, 1000*60);
		this.renderClock();
	}
	renderClock() {
		let date = new Date;
		let hour = date.getHours();
		let min = date.getMinutes();
		const ctx = this.canvas.getContext('2d');
		let angle;
		let secHandLength = this.canvas.width / 2;
		ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
		ctx.globalAlpha = 0.65;  // Make it "blend" into thee beckground a bit.

		// Outer dial
		ctx.lineWidth = 1;
		ctx.beginPath();
		ctx.arc(this.canvas.width / 2, this.canvas.height / 2, secHandLength - 1, 0, Math.PI * 2);
		ctx.strokeStyle = '#92949C';
		ctx.stroke();

		// Minute
		angle = ((Math.PI * 2) * (min / 60)) - ((Math.PI * 2) / 4);
		ctx.lineWidth = 1.5;
		ctx.beginPath();
		ctx.moveTo(this.canvas.width / 2, this.canvas.height / 2);
		ctx.lineTo((this.canvas.width / 2 + Math.cos(angle) * secHandLength / 1.2), this.canvas.height / 2 + Math.sin(angle) * secHandLength / 1.2);
		ctx.strokeStyle = '#999';
		ctx.stroke();

		// Hour
		angle = ((Math.PI * 2) * ((hour * 5 + (min / 60) * 5) / 60)) - ((Math.PI * 2) / 4);
		ctx.lineWidth = 1.5;
		ctx.beginPath();
		ctx.moveTo(canvas.width / 2, canvas.height / 2);
		ctx.lineTo((this.canvas.width / 2 + Math.cos(angle) * secHandLength / 1.5), this.canvas.height / 2 + Math.sin(angle) * secHandLength / 1.5);
		ctx.strokeStyle = '#000';
		ctx.stroke();
	}
	render() {
		return (
			<div>
				<canvas ref={canvas => { this.canvas = canvas; }} id="canvas" width="25" height="25" style={{position: 'absolute', left: 185, top: 30}}></canvas>
				<img src="/telldus/img/lamp.png" style={{width: '100%'}} />
			</div>
		);
	}
}
