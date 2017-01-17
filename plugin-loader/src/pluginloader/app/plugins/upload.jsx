define(
	['react', 'react-mdl', 'react-redux', 'plugins/actions', 'plugins/formatfingerprint'],
function(React, ReactMDL, ReactRedux, Actions, formatFingerPrint ) {
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
		upload() {
			this.props.store.dispatch(Actions.uploadPlugin(this.state.file));
		}
		render() {
			return (
				<div>
					<form ref={f => {this.formRef = f}}>
						<input type="file" onChange={() => this.fileChanged()} ref={f => {this.fileRef = f}} accept="application/zip" />
					</form>
					<ReactMDL.Button raised onClick={() => this.upload()} disabled={this.state.file == null}>Upload</ReactMDL.Button>
					<ReactMDL.Spinner style={{display: (this.props.uploading ? '' : 'none')}}/>
				</div>
			)
		}
	}

	Upload.propTypes = {
		uploading: React.PropTypes.bool.isRequired,
	};
	const mapStateToProps = (state) => ({
		uploading: state.uploading,
	});
	const mapDispatchToProps = (dispatch) => ({
	});
	return ReactRedux.connect(mapStateToProps, mapDispatchToProps)(Upload);
});
