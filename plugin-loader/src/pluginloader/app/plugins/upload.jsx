define(
	['react', 'react-mdl', 'react-redux', 'plugins/actions', 'plugins/formatfingerprint', 'plugins/categoryicon'],
function(React, ReactMDL, ReactRedux, Actions, formatFingerPrint, CategoryIcon ) {
	class Upload extends React.Component {
		constructor(props) {
			super(props);
			this.state = {
				file: null
			}
			this.fileRef = null;
			this.formRef = null;
		}
		componentWillReceiveProps(nextProps) {
			if (this.props.uploading != nextProps.uploading) {
				if (nextProps.uploading == false && this.formRef) {
					this.formRef.reset();
					this.setState({file: null});
				}
			}
		}
		fileChanged() {
			var file = this.fileRef.files[0];
			this.setState({file: file});
		}
		render() {
			return (
				<div style={{float: 'left'}}>
				<ReactMDL.Tooltip label="Manual upload" position="right" large>
					<ReactMDL.FABButton style={{marginRight: '8px'}}>
						<ReactMDL.Icon name="file_upload" />
					</ReactMDL.FABButton>
				</ReactMDL.Tooltip>

				<ReactMDL.Dialog style={{
					width: '400px',
					padding: '0'
				}}>
					<ReactMDL.DialogTitle style={{
						color: '#555'
					}}>
						<CategoryIcon category="upload" color="#757575" />
						Manual upload
					</ReactMDL.DialogTitle>
					<ReactMDL.DialogContent>
						<p>Please select a plugin file and press the upload button to load a new plugin.</p>
						<form ref={f => {this.formRef = f}}>
						<input type="file" onChange={() => this.fileChanged()} ref={f => {this.fileRef = f}} accept="application/zip" />
						</form>
					</ReactMDL.DialogContent>
					<ReactMDL.DialogActions style={{
						backgroundColor: '#757575',
						padding: '12px'
					}}>
						<ReactMDL.Button className="buttonRounded buttonWhite" raised>Close</ReactMDL.Button>
						<ReactMDL.Button raised className="buttonRounded buttonAccept" onClick={() => this.props.onUpload(this.state.file)} disabled={this.state.file == null} style={{
							backgroundColor: '#9ccc65'
						}}>Upload</ReactMDL.Button>
						<ReactMDL.Spinner style={{display: (this.props.uploading ? '' : 'none')}}/>
					</ReactMDL.DialogActions>
				</ReactMDL.Dialog>
				</div>
			)
		}
	}

	Upload.propTypes = {
		onUpload: React.PropTypes.func.isRequired,
		uploading: React.PropTypes.bool.isRequired,
	};
	const mapStateToProps = (state) => ({
		uploading: state.uploading,
	});
	const mapDispatchToProps = (dispatch) => ({
		onUpload: (file) => {
			dispatch(Actions.uploadPlugin(file));
		}
	});
	return ReactRedux.connect(mapStateToProps, mapDispatchToProps)(Upload);
});
