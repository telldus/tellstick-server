define(
	['react', 'react-mdl'],
function(React, ReactMDL) {
	class DropDownConfiguration extends React.Component {
		constructor(props) {
			super(props);
			this.state = {selected: this.props.value.selected,values:this.props.value}
		}
		countryChange(e){

			let state = {};
			let values = {...this.state.values[this.props.pluginClass]};
			values['selected'] = e.target.value
			state[this.props.pluginClass] = values;
			this.setState({values: state, selectede:e.target.value})
			
			var data = new FormData();
			data.append('pluginname', this.props.plugin);
			data.append('configuration', JSON.stringify(state));
			return fetch('/pluginloader/saveConfiguration', {
				method: 'POST',
				credentials: 'include',
				body: data,
			});
		}
		render() {
			let options = []
			let array=this.props.value.list;
		    for (var item in array){
		    	if(item===this.state.selected)
		      		options.push(<option value={item} selected>{array[item]}</option>)
		      	else
		      		options.push(<option value={item}>{array[item]}</option>)
		    }
			return (
				<div style={{position: 'relative'}}>
				    <select onChange={(e)=>this.countryChange(e)}>
				    	<option value="">Not in list</option>
				    	{options}
				    </select>
				</div>
			)
		}
	};
	return DropDownConfiguration;
});
