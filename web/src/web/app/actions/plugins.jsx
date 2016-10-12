export const REQUEST_PLUGINS = 'REQUEST_PLUGINS'
export const RECEIVE_PLUGINS = 'RECEIVE_PLUGINS'

function requestPlugins() {
	return {
		type: REQUEST_PLUGINS
	}
}

function receivePlugins(json) {
	return {
		type: RECEIVE_PLUGINS,
		plugins: json
	}
}

export function fetchPlugins() {
	return dispatch => {
		dispatch(requestPlugins())
		return fetch('/web/reactPlugins', {
			credentials: 'include'
		})
			.then(response => response.json())
			.then(json => dispatch(receivePlugins(json)))
	}
}
