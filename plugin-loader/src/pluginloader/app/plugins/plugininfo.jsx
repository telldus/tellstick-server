define(
	['react', 'react-mdl', 'react-redux', 'react-markdown', 'dialog-polyfill', 'plugins/actions', 'plugins/categoryicon'],
function(React, ReactMDL, ReactRedux, ReactMarkdown, DialogPolyfill, Actions, CategoryIcon) {
	const formatSize = size => {
		let ext = 'bytes';
		if (size >= 1024) {
			size /= 1024;
			ext = 'kb'
		}
		return Math.round(size) + ' ' + ext;
	}
	class PluginInfo extends React.Component {
		constructor(props) {
			super(props)
			this.state = { activeTab: 0 };
		}
		componentWillReceiveProps(nextProps) {
			if (this.props.show != nextProps.show && nextProps.show == true) {
				this.setState({activeTab: 0});
			}
		}
		componentDidMount() {
			if (!this.dialog.dialogRef.showModal) {
				DialogPolyfill.registerDialog(this.dialog.dialogRef);
			}
		}
		render() {
			return (
				<ReactMDL.Dialog open={this.props.show} ref={(c) => this.dialog = c} onCancel={this.props.onClose} style={{width: '500px', padding: 0}}>
					<ReactMDL.DialogTitle style={{color: '#555'}}>
						<CategoryIcon category={this.props.category} color={this.props.color} />{this.props.name}
					</ReactMDL.DialogTitle>
					<ReactMDL.DialogContent>
						<div>
							{this.props.longDescription && <ReactMDL.Tabs activeTab={this.state.activeTab} onChange={(tabId) => this.setState({ activeTab: tabId })} ripple>
								<ReactMDL.Tab>Overview</ReactMDL.Tab>
								<ReactMDL.Tab>Details</ReactMDL.Tab>
							</ReactMDL.Tabs>}
							{this.state.activeTab == 0  && <section>
								<div className="content" style={{padding: '12px 0'}}>
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
								</div>
							</section>}
							{this.state.activeTab == 1  && <section>
								<ReactMarkdown.Markdown source={this.props.longDescription} />
							</section>}
						</div>

						<div style={{color: 'red', display: this.props.errorMessage == '' ? 'none' : ''}}>Install failed: {this.props.errorMessage}</div>
					</ReactMDL.DialogContent>
					<ReactMDL.DialogActions style={{
						backgroundColor: this.props.color,
						padding: '12px'
					}}>
						<ReactMDL.Button type='button' className="buttonRounded buttonWhite" onClick={() => this.props.onClose()} raised>Close</ReactMDL.Button>
						{this.props.installed &&
							<ReactMDL.Button type='button' className="buttonRounded buttonDecline" onClick={() => this.props.onUninstall(this.props.name)} raised>Uninstall</ReactMDL.Button>
						}
						{!this.props.installed &&
							<ReactMDL.Button type='button' className="buttonRounded buttonAccept" onClick={() => this.props.onInstall(this.props.name)} raised disabled={this.props.installing}>Install</ReactMDL.Button>
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
		longDescription: '',
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
			category: plugin.category,
			color: plugin.color,
			installed: installed,
			installing: state.installing == plugin.name,
			longDescription: plugin.long_description,
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
