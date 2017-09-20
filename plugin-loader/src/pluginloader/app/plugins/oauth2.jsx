define(
	['react', 'react-mdl'],
function(React, ReactMDL) {
	class OAuth2Configuration extends React.Component {
		constructor(props) {
			super(props);
			console.log("OAUth2 props", props);
			this.state = {activated: props.activated}
		}
		activate() {
			var formData = new FormData();
			formData.append('action', 'activate');
			formData.append('pluginname', this.props.plugin);
			formData.append('pluginclass', this.props.pluginClass);
			formData.append('config', this.props.config);
			formData.append('redirectUri', window.location.protocol + '//' + window.location.host + '/pluginloader/oauth2?pluginname=' + this.props.plugin + '&pluginclass=' + this.props.pluginClass + '&config=' + this.props.config);
			fetch(
				'/pluginloader/oauth2', {
					method: 'POST',
					credentials: 'include',
					body: formData
				}
			)
			.then(response => response.json())
			.then(json => { console.log(json); return json; })
			.then(json => window.open(json.url))
		}
		logout() {
			fetch('/plugins/oauth2Deactivate',{credentials: 'include'})
			.then(response => response.json())
			.then(json => {
				if (json.success == true) {
					this.setState({activated: false})
				}
			})
		}
		render() {
			return (
				<div>
					{!this.state.activated && <ReactMDL.Button onClick={() => this.activate()}>Activate</ReactMDL.Button>}
					{this.state.activated && <ReactMDL.Button onClick={() => this.logout()}>Log out</ReactMDL.Button>}
				</div>
			)
		}
	};
	return OAuth2Configuration;
});
