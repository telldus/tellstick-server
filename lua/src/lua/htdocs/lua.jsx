define(
	['react', 'react-mdl', 'react-router', 'telldus', 'websocket', 'jsx!lua/actions', 'react-redux', 'jsx!lua/react-codemirror', 'dialog-polyfill'],
	function(React, ReactMDL, ReactRouter, Telldus, WebSocket, Actions, ReactRedux, CodeMirror, DialogPolyfill ) {
		var {Button, Card, CardActions, CardMenu, CardTitle, CardText, Cell, Dialog, DialogActions, DialogContent, DialogTitle, Grid, IconButton, List, ListItem, Textfield} = ReactMDL;
		var {Provider, connect} = ReactRedux;
		var {browserHistory, Link} = ReactRouter;

		var defaultState = {
			scripts: [],
			script: {
				code: '',
				name: ''
			},
			showNewDialog: false
		}

		function reducer(state = defaultState, action) {
			switch (action.type) {
				case Actions.CLEAR_SCRIPT:
					return Object.assign({}, state, {script: {code: '', name: ''}})
				case Actions.RECEIVE_SCRIPTS:
					return Object.assign({}, state, {scripts: action.scripts});
				case Actions.RECEIVE_SCRIPT:
					return Object.assign({}, state, {script: action.script})
				case Actions.SHOW_NEW_DIALOG:
					return Object.assign({}, state, {showNewDialog: action.show});
			}
			return state;
		}

		var store = Telldus.createStore(reducer)
		store.dispatch(Actions.fetchScripts());

		class CodeView extends React.Component {
			constructor(props) {
				super(props);
				this.state = {showDeleteConfirm: false}
				this.code = props.code;  // Initialize local changed code
				this.codeChanged = this.codeChanged.bind(this);
				this.saveAndRun = this.saveAndRun.bind(this);
			}
			componentDidMount() {
				if (!this.dialog.dialogRef.showModal) {
					DialogPolyfill.registerDialog(this.dialog.dialogRef);
				}
			}
			codeChanged(newCode) {
				this.code = newCode;
			}
			deleteScript() {
				this.props.store.dispatch(Actions.deleteScript(this.props.name))
					.then(() => browserHistory.push('/lua'))
					.then(() => this.setState({showDeleteConfirm: false}));
			}
			saveAndRun() {
				this.props.store.dispatch(Actions.saveScript(this.props.name, this.code))
			}
			render() {
				return (
					<Card shadow={1} style={{width: '650px'}}>
						<Dialog open={this.state.showDeleteConfirm} ref={(c) => this.dialog = c} onCancel={() => this.setState({showDeleteConfirm: false})}>
							<DialogTitle>Delete script</DialogTitle>
							<DialogContent>
								Are you sure you want to delete {this.props.name}?
							</DialogContent>
							<DialogActions>
								<Button type='button' onClick={() => this.deleteScript()}>Yes</Button>
								<Button type='button' onClick={() => this.setState({showDeleteConfirm: false})}>No</Button>
							</DialogActions>
						</Dialog>
						<CardTitle>Script: {this.props.name}</CardTitle>
						<CardText>
							<CodeMirror onCodeChanged={this.codeChanged} code={this.props.code} />
						</CardText>
						<CardActions border>
							<Button onClick={this.saveAndRun} disabled={this.props.name == ''}>Save and run</Button>
							<Button onClick={() => this.setState({showDeleteConfirm: true})} disabled={this.props.name == ''}>Delete script</Button>
						</CardActions>
					</Card>
				);
			}
		}
		const mapCMStateToProps = (state) => {
			if (state.script == null) {
				return {}
			}
			return {
				name: state.script.name,
				code: state.script.code
			}
		}
		var WrappedCodeView = connect(mapCMStateToProps)(CodeView);

		class ScriptsList extends React.Component {
			constructor(props) {
				super(props);
			}
			render() {
				var scripts = this.props.scripts.map(script =>
					<ListItem key={script.name}>
						<Link to={{ pathname: '/lua', query: { script: script.name } }}>{script.name}</Link>
					</ListItem>
				)
				return (
					<List>
						{scripts}
					</List>
				);
			}
		}
		const mapStateToProps = (state) => {
			return {
				scripts: state.scripts
			}
		}
		var WrappedScriptsList = connect(mapStateToProps)(ScriptsList);

		class Console extends React.Component {
			constructor(props) {
				super(props);
				this.state = {
					logs: []
				}
				this.websocket = new WebSocket();
				this.message = this.message.bind(this);
				this.clear = this.clear.bind(this);
			}
			componentDidMount() {
				this.websocket.onMessage('lua', 'log', this.message);
			}
			componentWillUnmount() {
				this.websocket.onMessage('lua', 'log', null);
			}
			clear() {
				this.setState({logs: []});
			}
			message(module, action, data) {
				var logs = this.state.logs.slice()
				logs.push(data);
				this.setState({logs: logs});
			}
			render() {
				var logs = this.state.logs.map((log, i) => <p key={i}>{log}</p>)
				return (
					<Cell col={8}>
						<Card shadow={1} style={{width: '650px'}}>
							<CardTitle expand>Console</CardTitle>
							<CardText>
								{logs}
							</CardText>
							<CardActions border>
								<Button onClick={this.clear}>Clear</Button>
							</CardActions>
						</Card>
					</Cell>
				)
			}
		}

		class NewScript extends React.Component {
			constructor(props) {
				super(props);
				this.state = {scriptName: ''};
				this.handleCreateNewScript = this.handleCreateNewScript.bind(this);
				this.handleCloseDialog = this.handleCloseDialog.bind(this);
				this.valueChanged = this.valueChanged.bind(this);
			}
			componentDidMount() {
				if (!this.dialog.dialogRef.showModal) {
					DialogPolyfill.registerDialog(this.dialog.dialogRef);
				}
			}
			componentWillReceiveProps(nextProps) {
				if (this.props.showDialog != nextProps.showDialog) {
					this.setState({scriptName: ''});
				}
			}
			handleCloseDialog() {
				this.props.dispatch(Actions.showNewDialog(false));
			}
			handleCreateNewScript() {
				this.props.dispatch(Actions.newScript(this.state.scriptName))
					.then(c => browserHistory.push('/lua?script=' + c.name))
					.then(() => this.props.dispatch(Actions.showNewDialog(false)));
			}
			valueChanged(e) {
				this.setState({scriptName: e.target.value});
			}
			render() {
				return (
					<Dialog open={this.props.showDialog} ref={(c) => this.dialog = c} onCancel={e => this.handleCloseDialog()}>
						<DialogTitle>New script</DialogTitle>
						<DialogContent>
							<Textfield floatingLabel required onChange={this.valueChanged} label="Script name" value={this.state.scriptName} />
						</DialogContent>
						<DialogActions>
							<Button type='button' onClick={this.handleCreateNewScript}>Create</Button>
							<Button type='button' onClick={this.handleCloseDialog}>Cancel</Button>
						</DialogActions>
					</Dialog>
				);
			}
		}
		const mapNewScriptStateToProps = (state) => {
			return {
				showDialog: state.showNewDialog
			}
		}
		var WrappedNewScript = connect(mapNewScriptStateToProps)(NewScript);

		class LuaApp extends React.Component {
			constructor(props) {
				super(props);
			}
			componentDidMount() {
				store.dispatch(Actions.fetchScript(this.props.location.query.script));
			}
			componentWillReceiveProps(nextProps) {
				if (this.props.location.query.script !== nextProps.location.query.script) {
					store.dispatch(Actions.fetchScript(nextProps.location.query.script));
				}
			}
			newScript() {
				store.dispatch(Actions.showNewDialog());
			}
			render() {
				return (
					<div>
						<WrappedNewScript store={store} />
						<Grid>
							<Cell col={8}>
								<WrappedCodeView store={store} />
							</Cell>
							<Cell col={4}>
								<Card shadow={1}>
									<CardTitle expand>Scripts</CardTitle>
									<CardText>
										<WrappedScriptsList store={store} />
									</CardText>
									<CardActions border>
										<Button onClick={e => this.newScript()}>New script</Button>
									</CardActions>
								</Card>
							</Cell>
						</Grid>
						<Grid>
							<Console />
						</Grid>
					</div>
				);
			}
		};

		return LuaApp;
	});
