import { combineReducers } from 'redux'
import components from './components'
import plugins from './plugins'

const appReducers = combineReducers({
	components,
	plugins,
})

export default appReducers
