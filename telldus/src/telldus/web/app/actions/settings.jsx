export const REQUEST_TELLDUS_INFO = 'REQUEST_TELLDUS_INFO'
export const RECEIVE_TELLDUS_INFO = 'RECEIVE_TELLDUS_INFO'

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
