export const REQUEST_TELLDUS_INFO = 'REQUEST_TELLDUS_INFO'
export const RECEIVE_TELLDUS_INFO = 'RECEIVE_TELLDUS_INFO'
export const REQUEST_SET_DISTRIBUTION = 'REQUEST_SET_DISTRIBUTION'
export const RECEIVE_SET_DISTRIBUTION = 'RECEIVE_SET_DISTRIBUTION'

function requestTelldusInfo() { return { type: REQUEST_TELLDUS_INFO} }
function receiveTelldusInfo(json) { return { type: RECEIVE_TELLDUS_INFO, info: json } }
export function fetchTelldusInfo() {
	return dispatch => {
		dispatch(requestTelldusInfo())
		return fetch('/telldus/info', {
			credentials: 'include'
		})
			.then(response => response.json())
			.then(json => dispatch(receiveTelldusInfo(json)))
	}
}

export function setDistribution(name) {
	var data = new FormData();
	data.append('name', name);
	return dispatch => {
		dispatch({ type: REQUEST_SET_DISTRIBUTION} )
		return fetch('/telldus/setDistribution', {
			method: 'POST',
			credentials: 'include',
			body: data,
		})
			.then(response => response.json())
			.then(json => dispatch({ type: RECEIVE_SET_DISTRIBUTION, info: json }))
	}
}
