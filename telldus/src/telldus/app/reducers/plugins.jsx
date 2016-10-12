import {RECEIVE_PLUGINS} from '../actions/plugins'

const plugins = (state = [], action) => {
	switch (action.type) {
		case RECEIVE_PLUGINS:
			return action.plugins
		default:
			return state
	}
}

export default plugins
