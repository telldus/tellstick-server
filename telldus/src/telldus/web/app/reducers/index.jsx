import { combineReducers } from 'redux'
import components from './components'
import settings from './settings'

const appReducers = combineReducers({
	components,
	settings,
})

export default appReducers
