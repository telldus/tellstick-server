define([], function() {
	const acceptKey = (keyid) => (
		dispatch => {
			dispatch({type: 'ACCEPT_KEY', keyid})
			return fetch('/pluginloader/importkey?key=' + keyid, {credentials: 'include'})
			.then(response => response.json())
			.then(json => {
				if (json['success'] != true) {
					dispatch({type: 'ACCEPT_KEY_FAILED', keyid})
					reject();
					return;
				}
				dispatch({type: 'KEY_ACCEPTED', keyid})
				dispatch(importPlugin());
				dispatch(fetchKeys());
			})
		}
	)

	const deleteKey = (key, fingerprint) => (
		dispatch => {
			dispatch({type: 'DELETE_KEY'})
			return fetch('/pluginloader/remove?key=' + key + '&fingerprint=' + fingerprint, {
				credentials: 'include'
			})
			.then(response => response.json())
			.then(json => {
				if (json['success'] == true) {
					dispatch({type: 'KEY_DELETED', key})
					dispatch(fetchKeys())
				}
			});
		}
	)

	const deletePlugin = (name) => (
		dispatch => {
			dispatch({type: 'DELETE_PLUGIN'})
			return fetch('/pluginloader/remove?pluginname=' + name, {
				credentials: 'include'
			})
			.then(response => response.json())
			.then(json => {
				if (json['success'] == true) {
					dispatch({type: 'PLUGIN_DELETED', name})
					dispatch(fetchPlugins())
				}
			});
		}
	)

	const discardKey = () => (
		dispatch => {
			dispatch({type: 'DISCARD_KEY'})
			return fetch('/pluginloader/importkey?discard', {credentials: 'include'})
			.then(response => response.json())
			.then(json => {
				if (json['success'] != true) {
					alert("Error discarding plugin");
				}
				dispatch({type: 'KEY_DISCARDED'})
			});
		}
	)

	const fetchKeys = () => (
		dispatch => {
			dispatch({type: 'REQUEST_KEYS'})
			return fetch('/pluginloader/keys',{
				credentials: 'include'
			})
			.then(response => response.json())
			.then(json => dispatch({type: 'RECEIVE_KEYS', keys: json}))
		}
	)

	const fetchPlugins = () => (
		dispatch => {
			dispatch({type: 'REQUEST_PLUGINS'})
			return fetch('/pluginloader/plugins', {
				credentials: 'include'
			})
			.then(response => response.json())
			.then(json => dispatch({type: 'RECEIVE_PLUGINS', plugins: json}))
		}
	)

	// This is a special action used to continue import after accepting key
	const importPlugin = () => (
		dispatch => {
			dispatch({type: 'IMPORT_PLUGIN'})
			return fetch('/pluginloader/import', {credentials: 'include'})
			.then(response => response.json())
			.then(json => {
				if (json['success'] == true) {
					dispatch({type: 'PLUGIN_UPLOADED'})
					dispatch(fetchPlugins());
				}
			});
		}
	)

	const uploadPlugin = (file) => (
		dispatch => {
			dispatch({type: 'UPLOAD_PLUGIN'})
			var data = new FormData();
			data.append('pluginfile', file)
			return fetch('/pluginloader/upload', {
				method: 'POST',
				credentials: 'include',
				body: data
			})
			.then(response => response.json())
			.then(json => {
				if (json['success'] == true) {
					dispatch({type: 'PLUGIN_UPLOADED'})
					dispatch(fetchPlugins());
					return;
				}
				if ('key' in json) {
					dispatch({type: 'IMPORT_KEY', key: json['key']});
					return;
				}
				if ('msg' in json) {
					dispatch({type: 'UPLOAD_PLUGIN_FAILED', msg: json['msg']})
				}
			});
		}
	)

	return {
		acceptKey,
		deleteKey,
		deletePlugin,
		discardKey,
		fetchKeys,
		fetchPlugins,
		uploadPlugin,
	};
});
