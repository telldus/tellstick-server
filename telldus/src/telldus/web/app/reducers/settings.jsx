import {RECEIVE_TELLDUS_INFO} from '../actions/settings'

const settings = (state = {
	'updated': false,
}, action) => {
	switch (action.type) {
		case RECEIVE_TELLDUS_INFO:
			return {...state, 'updated': true}
	}
	return state
}

export default settings
