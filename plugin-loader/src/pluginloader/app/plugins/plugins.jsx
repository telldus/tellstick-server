define(
	['react', 'react-mdl', 'react-redux', 'telldus', 'websocket', 'plugins/actions', 'plugins/configureplugin', 'plugins/errormessage', 'plugins/keyslist', 'plugins/keyimport', 'plugins/plugininfo', 'plugins/pluginslist', 'plugins/rebootdialog', 'plugins/store', 'plugins/upload'],
function(React, ReactMDL, ReactRedux, Telldus, WebSocket, Actions, ConfigurePlugin, ErrorMessage, KeysList, KeyImport, PluginInfo, PluginsList, RebootDialog, Store, Upload ) {
	Telldus.loadCSS('/pluginloader/plugins.css');

	var defaultState = {
		configure: null,
		importingKey: {
			keyid: null
		},
		installing: null,
		installErrorMsg: '',
		keys: [],
		pluginInfo: null,
		plugins: [],
		rebootStatus: 0,
		requireReboot: false,
		search: '',
		showUploadDialog: false,
		showRebootDialog: false,
		storePlugins: [],
		storePluginsRefreshing: false,
		uploading: false,
		uploadErrorMsg: '',
	}

	function reducer(state = defaultState, action) {
		switch (action.type) {
			case 'CLOSE_PLUGIN_INFO':
				return {...state, pluginInfo: null};
			case 'CONFIGURATION_SAVED':
				return {...state, configure: null};
			case 'CONFIGURE_PLUGIN':
				return {...state, configure: action.plugin}
			case 'DISCARD_ERROR':
				return {...state, uploadErrorMsg: ''}
			case 'IMPORT_KEY':
				return {...state, importingKey: action.key}
			case 'INSTALL_STORE_PLUGIN':
				return {...state, installing: action.name, installErrorMsg: ''}
			case 'INSTALL_STORE_PLUGIN_FAILED':
				return {...state, installing: null, installErrorMsg: action.msg}
			case 'INSTALL_STORE_PLUGIN_SUCCESS':
				return {...state, pluginInfo: null, installing: null, installErrorMsg: ''}
			case 'KEY_ACCEPTED':
				return {...state, importingKey: {...defaultState.importingKey}}
			case 'KEY_DISCARDED':
				return {...state, importingKey: {...defaultState.importingKey}, uploading: false}
			case 'PLUGIN_DELETED':
				if (action.name == state.pluginInfo) {
					return {...state, pluginInfo: null, requireReboot: true, showRebootDialog: true};
				}
				return {...state, requireReboot: true, showRebootDialog: true};
			case 'PLUGIN_INFO_RECEIVED':
				return {...state, plugins: state.plugins.map(plugin => (plugin.name == action.info.name ? action.info : plugin))}
			case 'PLUGIN_UPLOADED':
				return {...state, uploading: false, uploadErrorMsg: '', showUploadDialog: false}
			case 'REBOOT':
				return {...state, rebootStatus: 1}
			case 'REBOOT_FAILED':
				return {...state, rebootStatus: -1}
			case 'REBOOT_STARTED':
				return {...state, rebootStatus: 2}
			case 'RECEIVE_KEYS':
				return {...state, keys: action.keys};
			case 'RECEIVE_PLUGINS':
				return {...state, plugins: action.plugins};
			case 'RECEIVE_STORE_PLUGINS':
				return {...state, storePlugins: action.plugins, storePluginsRefreshing: false};
			case 'REFRESH_STORE_PLUGINS':
				return {...state, storePluginsRefreshing: true};
			case 'SEARCH':
				return {...state, search: action.search};
			case 'SHOW_PLUGIN_INFO':
				return {...state, pluginInfo: action.name};
			case 'SHOW_REBOOT_DIALOG':
				return {...state, showRebootDialog: action.show};
			case 'SHOW_UPLOAD':
				return {...state, showUploadDialog: action.show};
			case 'UPLOAD_PLUGIN':
				return {...state, uploading: true, uploadErrorMsg: ''}
			case 'UPLOAD_PLUGIN_FAILED':
				return {...state, uploading: false, uploadErrorMsg: action.msg}
		}
		return state;
	}

	var store = Telldus.createStore(reducer)
	store.dispatch(Actions.fetchStorePlugins());
	store.dispatch(Actions.fetchPlugins());
	store.dispatch(Actions.fetchKeys());
	var websocket = new WebSocket();
	websocket.onMessage('plugins', 'pluginInfo', (module, action, data) => {
		store.dispatch(Actions.pluginInfoReceived(data));
	});
	websocket.onMessage('plugins', 'downloadProgress', (module, action, data) => {
		//console.log(module, action, data);
	});
	websocket.onMessage('plugins', 'downloadFailed', (module, action, data) => {
		store.dispatch(Actions.installStorePluginFailed(data['msg']));
	});
	websocket.onMessage('plugins', 'install', (module, action, data) => {
		if (data['success'] == true) {
			store.dispatch(Actions.installStorePluginSuccess(data['msg']));
			store.dispatch(Actions.fetchPlugins());
		} else {
			store.dispatch(Actions.installStorePluginFailed(data['msg']));
		}
	});
	websocket.onMessage('plugins', 'storePluginsUpdated', (module, action, data) => {
		store.dispatch(Actions.fetchStorePlugins());
	});

	class PluginsApp extends React.Component {
		render() {
			return (
				<div>
					<div style={{padding: '16px'}}>
						<div style={{float: 'left'}}>
							<ReactMDL.Tooltip label="Manual upload" position="right" large>
								<ReactMDL.FABButton style={{marginRight: '8px'}} onClick={() => this.props.onUpload()}>
									<ReactMDL.Icon name="file_upload" />
								</ReactMDL.FABButton>
							</ReactMDL.Tooltip>
						</div>
						<div style={{float: 'left'}}>
							<ReactMDL.Tooltip label="Refresh List" position="right" large>
								<ReactMDL.FABButton style={{float: 'left', marginRight: '8px'}} onClick={() => this.props.onRefreshStorePlugins()} disabled={this.props.storePluginsRefreshing}>
									<ReactMDL.Icon name="refresh" />
								</ReactMDL.FABButton>
							</ReactMDL.Tooltip>
						</div>
						<div style={{float: 'left'}}>
							<ReactMDL.Tooltip label="Restart TellStick" position="right" large>
								<ReactMDL.FABButton style={{float: 'left', marginRight: '8px'}} onClick={() => this.props.onRebootClicked()}>
									<i className="telldus-icons">restart</i>
								</ReactMDL.FABButton>
							</ReactMDL.Tooltip>
						</div>
						<ReactMDL.Textfield
							 onChange={e => this.props.onSearch(e.target.value)}
							 label="Search"
							 expandable
							 expandableIcon="search"
							 className="searchField"
						/>
						<br style={{clear: 'both'}} />
					</div>
					<PluginsList />
					<Store />
					{this.props.keyLength > 0 && <ReactMDL.Grid>
						<ReactMDL.Cell component={ReactMDL.Card} col={7} shadow={1}>
							<ReactMDL.CardTitle expand>Trusted developers</ReactMDL.CardTitle>
							<ReactMDL.CardText>
								<KeysList />
							</ReactMDL.CardText>
						</ReactMDL.Cell>
					</ReactMDL.Grid>}
					<PluginInfo />
					<RebootDialog />
					<KeyImport />
					<ConfigurePlugin />
					<ErrorMessage />
					<Upload />
				</div>
			)
		}
	};

	const mapStateToProps = (state) => ({
		keyLength: state.keys.length,
		requireReboot: state.requireReboot,
		storePluginsRefreshing: state.storePluginsRefreshing,
	})
	const mapDispatchToProps = (dispatch) => ({
		onRebootClicked: () => dispatch(Actions.showRebootDialog(true)),
		onRefreshStorePlugins: () => dispatch(Actions.refreshStorePlugins()),
		onSearch: (value) => dispatch(Actions.search(value)),
		onUpload: () => dispatch(Actions.showUpload(true)),
	});
	var WrappedPluginsApp = ReactRedux.connect(mapStateToProps, mapDispatchToProps)(PluginsApp);

	return () => (
		<ReactRedux.Provider store={store}>
			<WrappedPluginsApp />
		</ReactRedux.Provider>
	)
});
