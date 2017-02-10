import {RECEIVE_COMPONENTS} from '../actions/components'

const components = (state = {}, action) => {
	switch (action.type) {
		case RECEIVE_COMPONENTS:
			return action.components
		default:
			return state
	}
}

export default components
