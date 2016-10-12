define([], function() {
	const DELETE_SCRIPT = 'DELETE_SCRIPT';
	const REQUEST_SCRIPTS = 'REQUEST_SCRIPTS';
	const RECEIVE_SCRIPTS = 'RECEIVE_SCRIPTS';
	const REQUEST_SCRIPT = 'REQUEST_SCRIPT';
	const RECEIVE_SCRIPT = 'RECEIVE_SCRIPT';
	const NEW_SCRIPT = 'NEW_SCRIPT';
	const NEW_SCRIPT_CREATED = 'NEW_SCRIPT_CREATED';
	const SAVE_SCRIPT = 'SAVE_SCRIPT';
	const SAVED_SCRIPT = 'SAVED_SCRIPT';
	const SHOW_NEW_DIALOG = 'SHOW_NEW_DIALOG';

	function requestScripts() { return { type: REQUEST_SCRIPTS } }
	function receiveScripts(json) { return { type: RECEIVE_SCRIPTS, scripts: json } }
	function fetchScripts() {
		return dispatch => {
			dispatch(requestScripts())
			return fetch('/lua/scripts',{
				credentials: 'include'
			})
			.then(response => response.json())
			.then(json => dispatch(receiveScripts(json)))
		}
	}

	function requestScript(script) { return { type: REQUEST_SCRIPT } }
	function receiveScript(json) { return { type: RECEIVE_SCRIPT, script: json } }
	function fetchScript(name) {
		return dispatch => {
			dispatch(requestScript(name))
			return fetch('/lua/script?name=' + name, {
				credentials: 'include'
			})
			.then(response => response.json())
			.then(json => dispatch(receiveScript(json)))
		}
	}

	function requestSaveScript(script, code) { return { type: SAVE_SCRIPT, script: script, code } }
	function receiveSaveScript(json) { return { type: SAVED_SCRIPT, status: json} }
	function saveScript(script, code) {
		var formData = new FormData();
		formData.append('script', script);
		formData.append('code', code);
		return dispatch => {
			dispatch(requestSaveScript(script, code))
			return fetch('/lua/save', {
				method: 'POST',
				credentials: 'include',
				body: formData
			})
			.then(response => response.json())
			.then(json => dispatch(receiveSaveScript(json)))
		}
	}

	function showNewDialog(show = true) { return { type: SHOW_NEW_DIALOG, show } }
	function requestNewScript(name) { return { type: NEW_SCRIPT, name } }
	function receiveNewScript(json) { return { type: NEW_SCRIPT_CREATED, name: json.name } }
	function newScript(name) {
		var formData = new FormData();
		formData.append('name', name);
		return dispatch => {
			dispatch(requestNewScript(name))
			return fetch('/lua/new', {
				method: 'POST',
				credentials: 'include',
				body: formData
			})
			.then(response => response.json())
			.then(json => dispatch(receiveNewScript(json)))
			.then(c => {dispatch(fetchScripts()); return c})
		}
	}

	function requestDeleteScript(name) { return { type: DELETE_SCRIPT, name } }
	//function receiveNewScript(json) { return { type: NEW_SCRIPT_CREATED, name: json.name } }
	function deleteScript(name) {
		var formData = new FormData();
		formData.append('name', name);
		return dispatch => {
			dispatch(requestDeleteScript(name))
			return fetch('/lua/delete', {
				method: 'POST',
				credentials: 'include',
				body: formData
			})
			.then(response => response.json())
			//.then(json => dispatch(receiveNewScript(json)))
			.then(() => dispatch(fetchScripts()))
		}
	}

	return {
		deleteScript,
		fetchScripts,
		fetchScript,
		newScript,
		saveScript,
		showNewDialog,
		DELETE_SCRIPT,
		REQUEST_SCRIPTS,
		RECEIVE_SCRIPTS,
		REQUEST_SCRIPT,
		RECEIVE_SCRIPT,
		SAVE_SCRIPT,
		SAVED_SCRIPT,
		SHOW_NEW_DIALOG
	};
});
