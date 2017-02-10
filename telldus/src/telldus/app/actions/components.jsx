export const REQUEST_COMPONENTS = 'REQUEST_COMPONENTS'
export const RECEIVE_COMPONENTS = 'RECEIVE_COMPONENTS'

function requestComponents() {
	return {
		type: REQUEST_COMPONENTS
	}
}

function receiveComponents(json) {
	return {
		type: RECEIVE_COMPONENTS,
		components: json
	}
}

export function fetchComponents() {
	return dispatch => {
		dispatch(requestComponents())
		return fetch('/telldus/reactComponents', {
			credentials: 'include'
		})
			.then(response => response.json())
			.then(json => dispatch(receiveComponents(json)))
	}
}
