define(
	['react', 'react-mdl', 'react-router'],
	function(React, ReactMDL, ReactRouter) {
		class WelcomeApp extends React.Component {
			render() {
				return (
					<div>
						<h1>hello world!</h1>
					</div>
				);
			}
		};

		return WelcomeApp;
	});
