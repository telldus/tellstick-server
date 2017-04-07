define(
	['react', 'react-mdl', 'react-redux', 'telldus', 'websocket', 'plugins/actions', 'plugins/configureplugin', 'plugins/errormessage', 'plugins/keyslist', 'plugins/keyimport', 'plugins/plugininfo', 'plugins/pluginslist', 'plugins/store', 'plugins/upload'],
function(React, ReactMDL, ReactRedux, Telldus, WebSocket, Actions, ConfigurePlugin, ErrorMessage, KeysList, KeyImport, PluginInfo, PluginsList, Store, Upload ) {
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
		requireReboot: false,
		storePlugins: [],
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
					return {...state, pluginInfo: null, requireReboot: true};
				}
				return {...state, requireReboot: true};
			case 'PLUGIN_INFO_RECEIVED':
				return {...state, plugins: state.plugins.map(plugin => (plugin.name == action.info.name ? action.info : plugin))}
			case 'PLUGIN_UPLOADED':
				return {...state, uploading: false, uploadErrorMsg: ''}
			case 'RECEIVE_KEYS':
				return {...state, keys: action.keys};
			case 'RECEIVE_PLUGINS':
				return {...state, plugins: action.plugins};
			case 'RECEIVE_STORE_PLUGINS':
				return {...state, storePlugins: action.plugins};
			case 'SHOW_PLUGIN_INFO':
				return {...state, pluginInfo: action.name};
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

	class PluginsApp extends React.Component {
		render() {
			return (
				<div>
					<div style={{padding: '16px'}}>
						<ReactMDL.Cell component={Upload} col={3} shadow={1} />
						<div style={{float: 'left'}}>
							<ReactMDL.Tooltip label="Refresh List" position="right" large>
								<ReactMDL.FABButton style={{float: 'left', marginRight: '8px'}}>
									<ReactMDL.Icon name="refresh" />
								</ReactMDL.FABButton>
							</ReactMDL.Tooltip>
						</div>
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
					<KeyImport />
					<ConfigurePlugin />
					<ErrorMessage />
				</div>
			)
		}
	};

	const mapStateToProps = (state) => ({
		keyLength: state.keys.length,
	})
	var WrappedPluginsApp = ReactRedux.connect(mapStateToProps)(PluginsApp);

	return () => (
		<ReactRedux.Provider store={store}>
			<WrappedPluginsApp />
		</ReactRedux.Provider>
	)
});
