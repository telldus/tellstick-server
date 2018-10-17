define(
	['react', 'react-mdl'],
function(React, ReactMDL) {
	class DropDownConfiguration extends React.Component {
		constructor(props) {
			super(props);
			this.state = {selected: this.props.value}
		}
		onChange(newValue) {
			this.setState({selected: newValue});
			this.props.onChange(newValue);
		}
		render() {
			// Sort the options
			let options = Object.keys(this.props.options)
				.sort((a, b) => this.props.options[a].localeCompare(this.props.options[b]))
				.map(key => (
					<option value={key} key={key}>{this.props.options[key]}</option>
				)
			);
			return (
				<div>
					<select onChange={(e)=>this.onChange(e.target.value)} value={this.state.selected}>
						{options}
					</select>
				</div>
			)
		}
	};
	return DropDownConfiguration;
});
