define(
	['react', 'react-mdl'],
	function(React, ReactMDL ) {
		var {Button, Card, CardActions, CardMenu, CardTitle, CardText, Cell, Grid, IconButton} = ReactMDL;

		class LuaApp extends React.Component {
			render() {
				return (
					<Card shadow={1}>
						<CardTitle expand>Lua page</CardTitle>
						<CardText>
							Hello world
						</CardText>
					</Card>
				);
			}
		};

		return LuaApp;
	});
