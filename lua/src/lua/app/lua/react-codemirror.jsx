define(
	['react', 'codemirror', 'mode-lua-compressed', 'telldus'],
	function(React, CM, mode, Telldus ) {
		Telldus.loadCSS('/lua/codemirror.css');
		Telldus.loadCSS('/lua/neat.css');

		class CodeMirror extends React.Component {
			constructor(props) {
				super(props);
				this.editor = null;
				this.codeChanged = this.codeChanged.bind(this);
				this.textAreaRendered = this.textAreaRendered.bind(this);
			}
			codeChanged(editor, newCode) {
				this.props.onCodeChanged(editor.getValue());
			}
			componentWillReceiveProps(nextProps) {
				if (this.props.code !== nextProps.code) {
					this.editor.setValue(nextProps.code);
				}
			}
			textAreaRendered(textarea) {
				if (textarea == null) {
					if (this.editor != null) {
						this.editor.toTextArea();
					}
					return;
				}
				this.editor = CM.fromTextArea(textarea, {
					matchBrackets: true,
					theme: "neat",
					lineNumbers: true,
					indentWithTabs: true,
					indentUnit: 4,
					tabSize: 4
				});
				this.editor.on('change', this.codeChanged)
			}
			render() {
				return (
					<textarea ref={this.textAreaRendered} id="code" name="code" defaultValue={this.props.code} />
				);
			}
		}

		CodeMirror.propTypes = {
			code: React.PropTypes.string,
			onCodeChanged: React.PropTypes.func
		};
		CodeMirror.defaultProps = {
			code: '',
			onCodeChanged: function() {}
		};
		return CodeMirror;
	});
