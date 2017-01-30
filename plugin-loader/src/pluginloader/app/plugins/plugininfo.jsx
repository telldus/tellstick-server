define(
	['react', 'react-mdl', 'react-redux', 'dialog-polyfill', 'plugins/actions'],
function(React, ReactMDL, ReactRedux, DialogPolyfill, Actions) {
	const formatSize = size => {
		let ext = 'bytes';
		if (size >= 1024) {
			size /= 1024;
			ext = 'kb'
		}
		return Math.round(size) + ' ' + ext;
	}
	class PluginInfo extends React.Component {
		componentDidMount() {
			if (!this.dialog.dialogRef.showModal) {
				DialogPolyfill.registerDialog(this.dialog.dialogRef);
			}
		}
		render() {
			return (
				<ReactMDL.Dialog open={this.props.show} ref={(c) => this.dialog = c} onCancel={this.props.onClose} style={{width: '500px'}}>
					<ReactMDL.DialogTitle>{this.props.name}</ReactMDL.DialogTitle>
					<ReactMDL.DialogContent>
						<div style={{float: 'left', paddingRight: '16px', paddingBottom: '16px'}}>
							{this.props.icon && <img src={this.props.icon} />}
							{!this.props.icon && <ReactMDL.Icon name="extension" style={{fontSize: '96px', lineHeight: '96px'}} />}
						</div>
						<div>Author:&nbsp;{this.props.author && this.props.author.replace(' ', "\u00a0")}</div>
						<div>Email:&nbsp;{this.props.authorEmail}</div>
						<div>Version:&nbsp;{this.props.version}</div>
						<div>Size:&nbsp;{formatSize(this.props.size)}</div>
						<br style={{clear: 'both'}} />
						<p>{this.props.description}</p>
						<div style={{color: 'red', display: this.props.errorMessage == '' ? 'none' : ''}}>Install failed: {this.props.errorMessage}</div>
					</ReactMDL.DialogContent>
					<ReactMDL.DialogActions>
						<ReactMDL.Button type='button' onClick={() => this.props.onClose()} raised>Close</ReactMDL.Button>
						{this.props.installed &&
							<ReactMDL.Button type='button' onClick={() => this.props.onUninstall(this.props.name)} style={{backgroundColor: '#dc5e51'}} raised>Uninstall</ReactMDL.Button>
						}
						{!this.props.installed &&
							<ReactMDL.Button type='button' onClick={() => this.props.onInstall(this.props.name)} style={{backgroundColor: '#9ccc66'}} raised disabled={this.props.installing}>Install</ReactMDL.Button>
						}
					</ReactMDL.DialogActions>
				</ReactMDL.Dialog>
			)
		}
	}

	/*PluginInfo.propTypes = {
	};*/
	PluginInfo.defaultProps = {
		errorMessage: '',
		installing: false,
		version: '?',
	};
	const mapStateToProps = (state) => {
		if (state.pluginInfo == null) {
			return {}
		}
		var installed = true;
		let plugin = state.plugins.find(plugin => plugin.name == state.pluginInfo);
		if (!plugin) {
			plugin = state.storePlugins.find(plugin => plugin.name == state.pluginInfo);
			installed = false;
		}
		if (!plugin) {
			return {}
		}
		return {
			author: plugin.author,
			authorEmail: plugin['author-email'],
			description: plugin.description,
			errorMessage: state.installErrorMsg,
			icon: plugin.icon,
			installed: installed,
			installing: state.installing == plugin.name,
			name: plugin.name,
			show: true,
			size: plugin.size,
			version: plugin.version,
		}
	};
	const mapDispatchToProps = (dispatch) => ({
		onClose: () => dispatch(Actions.closePluginInfo()),
		onInstall: (name) => dispatch(Actions.installStorePlugin(name)),
		onUninstall: (name) => dispatch(Actions.deletePlugin(name)),
	});
	return ReactRedux.connect(mapStateToProps, mapDispatchToProps)(PluginInfo);
});
