define(
	['react', 'react-mdl', 'react-redux', 'jsx!lua/actions', 'dialog-polyfill'],
	function(React, ReactMDL, ReactRedux, Actions, DialogPolyfill ) {
		class SignalsView extends React.Component {
			render() {
				var signals = this.props.signals.map((v) => (
					<ReactMDL.ListItem key={v.name} threeLine>
						<ReactMDL.ListItemContent subtitle={v.doc}>{v.name}({v.args.join(', ')})</ReactMDL.ListItemContent>
					</ReactMDL.ListItem>
				))
				return (
					<section>
						<ReactMDL.List>
							{signals}
						</ReactMDL.List>
					</section>
				)
			}
		}

		class HelpView extends React.Component {
			constructor(props) {
				super(props)
				this.state = { activeTab: 0 };
			}
			componentDidMount() {
				if (!this.dialog.dialogRef.showModal) {
					DialogPolyfill.registerDialog(this.dialog.dialogRef);
				}
				if (this.props.signals.length == 0) {
					this.props.store.dispatch(Actions.fetchSignals());
				}
			}
			render() {
				var page = null;
				switch(this.state.activeTab) {
					case 0:
						page = (<SignalsView signals={this.props.signals} />)
						break;
				}
				return (
					<ReactMDL.Dialog open={this.props.open} ref={(c) => this.dialog = c} onCancel={this.props.onCancel} style={{width: 700}}>
						<ReactMDL.DialogContent>
							<ReactMDL.Tabs activeTab={this.state.activeTab} onChange={(tabId) => this.setState({ activeTab: tabId })} ripple>
								<ReactMDL.Tab>Signals</ReactMDL.Tab>
							</ReactMDL.Tabs>
							<section>
								{page}
							</section>
						</ReactMDL.DialogContent>
					</ReactMDL.Dialog>
				);
			}
		}

		const mapStateToProps = (state) => {
			return {
				signals: state.signals
			}
		}
		return ReactRedux.connect(mapStateToProps)(HelpView);
	});
