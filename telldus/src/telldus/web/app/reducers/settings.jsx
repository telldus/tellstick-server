import {RECEIVE_TELLDUS_INFO} from '../actions/settings'

const settings = (state = {
	'firmware': {
		distribution: '',
		version: '',
	},
	'updated': false,
}, action) => {
	switch (action.type) {
		case RECEIVE_TELLDUS_INFO:
			return {
				...state,
				firmware: {...state.firmware, ...action.info.firmware},
				'updated': true
			}
	}
	return state
}

export default settings
