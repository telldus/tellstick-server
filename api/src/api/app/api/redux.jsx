define([], function() {
	var defaultState = {
		explorer: {module: null, action: null, result: {}},
		methods: {}
	}

	function reducer(state = defaultState, action) {
		switch (action.type) {
			case 'CLOSE_EXPLORER':
				return {...state, explorer: {module: null, action: null, result: {}}}
			case 'EXPLORE':
				return {...state, explorer: {module: action.module, action: action.action}}
			case 'EXPLORER_RESULT':
				return {...state, explorer: {...state.explorer, result: action.result}}
			case 'RECEIVE_METHODS':
				return {...state, methods: action.methods};
		}
		return state;
	}

	function closeExplorer() { return { type: 'CLOSE_EXPLORER' } }
	function explore(module, action) { return { type: 'EXPLORE', module, action } }

	function fetchMethods() {
		return dispatch => {
			dispatch({ type: 'REQUEST_METHODS' })
			return fetch('/api/methods', {
				credentials: 'include'
			})
			.then(response => response.json())
			.then(json => dispatch({ type: 'RECEIVE_METHODS', methods: json }))
		}
	}

	function testMethod(module, action, params) {
		return dispatch => {
			dispatch({ type: 'TEST_METHOD', module, action, params })
			var data = new FormData();
			data.append('module', module);
			data.append('action', action);
			data.append('params', JSON.stringify(params));
			return fetch('/api/explore', {
				credentials: 'include',
				method: 'POST',
				body: data,
			})
			.then(result => result.json())
			.then(result => dispatch({ type: 'EXPLORER_RESULT', result }))
		}
	}

	return {
		closeExplorer,
		explore,
		fetchMethods,
		reducer,
		testMethod,
	};
});
