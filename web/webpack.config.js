var webpack = require('webpack');
var path = require('path');

module.exports = {
	entry: [
		path.resolve(__dirname, 'src/web/app/main.jsx')
	],
	output: {
		path: __dirname + '/src/web/htdocs/js',
		publicPath: '/',
		filename: './bundle.js'
	},
	module: {
		loaders:[
			{ test: /\.css$/, include: path.resolve(__dirname, 'src/web/app'), loader: 'style-loader!css-loader' },
			{ test: /\.css$/, loader: "style-loader!css-loader" },
			{ test: /\.js[x]?$/, include: path.resolve(__dirname, 'src/web/app'), exclude: /node_modules/, loader: 'babel-loader' },
			{ test: /bin\/r\.js$/, loader: 'ignore-loader'}
		]
	},
	resolve: {
		extensions: ['', '.js', '.jsx'],
	},
	plugins: [
		//new webpack.optimize.UglifyJsPlugin(),
// 		new webpack.HotModuleReplacementPlugin(),
	],
};
