define(
	['react', 'react-mdl', 'react-redux', 'plugins/actions', 'plugins/formatfingerprint'],
function(React, ReactMDL, ReactRedux, Actions, formatFingerPrint ) {
	class KeysList extends React.Component {
		delete(key, fingerprint) {
			fetch('/pluginloader/remove?key=' + key + '&fingerprint=' + fingerprint, {
				credentials: 'include'
			})
			.then(response => response.json())
			.then(json => {
				if (json['success'] == true) {
					this.fetchKeys();
				}
			});
		}
		render() {
			return (
				<ReactMDL.List>
					{this.props.keys.map(key =>
						<ReactMDL.ListItem key={key.keyid} twoLine>
							<ReactMDL.ListItemContent subtitle={formatFingerPrint(key.fingerprint)}>{key.uids}</ReactMDL.ListItemContent>
							<ReactMDL.ListItemAction>
								<a onClick={() => this.props.onDeleteKeyClick(key.keyid, key.fingerprint)}><ReactMDL.Icon name="delete" /></a>
							</ReactMDL.ListItemAction>
						</ReactMDL.ListItem>
					)}
				</ReactMDL.List>
			)
		}
	}
	KeysList.propTypes = {
		keys: React.PropTypes.array.isRequired,
		onDeleteKeyClick: React.PropTypes.func.isRequired
	};
	const mapStateToProps = (state) => ({
		keys: state.keys,
	})
	const mapDispatchToProps = (dispatch) => {
		return {
			onDeleteKeyClick: (key, fingerprint) => {
				dispatch(Actions.deleteKey(key, fingerprint))
			}
		}
	}
	return ReactRedux.connect(mapStateToProps, mapDispatchToProps)(KeysList);
});
