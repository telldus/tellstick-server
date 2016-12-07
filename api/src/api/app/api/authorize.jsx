define(
	['react', 'react-mdl'],
function(React, ReactMDL) {
	class APIApp extends React.Component {
		constructor(props) {
			super(props);
			this.state = {
				token: null,
				authorized: true,
				app: '',
				ttl: '1440',
				allowRenew: false,
			};
		}
		authorize() {
			var data = new FormData();
			data.append('token', this.state.token);
			data.append('ttl', this.state.ttl);
			data.append('extend', this.state.allowRenew == true ? 1 : 0);
			fetch('/api/authorizeToken', {
				credentials: 'include',
				method: 'POST',
				body: data,
			})
			.then(response => response.json())
			.then(token => this.setState(token));
		}
		componentDidMount() {
			if (!this.dialog.dialogRef.showModal) {
				DialogPolyfill.registerDialog(this.dialog.dialogRef);
			}
			if (this.state.tokenInfo == null) {
				fetch('/api/tokenInfo?token=' + this.props.location.query.token, {
					credentials: 'include'
				})
				.then(response => response.json())
				.then(token => this.setState({...token, token: this.props.location.query.token}));
			}
		}
		render() {
			return (
				<div>
					<ReactMDL.Spinner style={{display: (this.state.token == null ? '' : 'none')}} />
					<div style={{display: (this.state.token != null && this.state.authorized == true ? '' : 'none')}}>
						The application has been autorized. Please go back to the application and continue the autorization.
					</div>
					<ReactMDL.Dialog open={this.state.authorized == false} ref={(c) => this.dialog = c} style={{width: 700}}>
						<ReactMDL.DialogTitle>Authorize application {this.state.app}</ReactMDL.DialogTitle>
						<ReactMDL.DialogContent>
							<div>
								<ReactMDL.RadioGroup name="ttl" value={this.state.ttl} onChange={ev => this.setState({ttl: ev.target.value})}>
									<ReactMDL.Radio value="1440" ripple>One day</ReactMDL.Radio>
									<ReactMDL.Radio value="10080" ripple>One week</ReactMDL.Radio>
									<ReactMDL.Radio value="40320" ripple>One month</ReactMDL.Radio>
									<ReactMDL.Radio value="525600" ripple>One year</ReactMDL.Radio>
								</ReactMDL.RadioGroup>
							</div>
							<div>
								<ReactMDL.Checkbox checked={this.state.allowRenew} onChange={ev => this.setState({allowRenew: !this.state.allowRenew})} label="Allow application to auto renew access" ripple />
							</div>
						</ReactMDL.DialogContent>
						<ReactMDL.DialogActions>
							<ReactMDL.Button type='button' onClick={() => this.authorize()}>Authorize</ReactMDL.Button>
						</ReactMDL.DialogActions>
					</ReactMDL.Dialog>
				</div>
			)
		}
	};

	return APIApp;
});
