var webpack = require('webpack');
var path = require('path');

module.exports = {
	entry: [
		'whatwg-fetch',
		path.resolve(__dirname, 'src/telldus/app/main.jsx'),
		'webpack-material-design-icons'
	],
	output: {
		path: __dirname + '/src/telldus/htdocs',
		publicPath: '/telldus/',
		filename: './js/bundle.js'
	},
	module: {
		loaders:[
			{ test: /\.css$/, include: path.resolve(__dirname, 'src/telldus/app'), loader: 'style-loader!css-loader' },
			{ test: /\.css$/, loader: "style-loader!css-loader" },
			{ test: /\.js[x]?$/, include: path.resolve(__dirname, 'src/telldus/app'), exclude: /node_modules/, loader: 'babel-loader' },
			{ test: /bin\/r\.js$/, loader: 'ignore-loader'},
			{ test: /\.(jpe?g|png|gif|svg|eot|woff|ttf|svg|woff2)$/, loader: "file?name=[name].[ext]" }
		]
	},
	resolve: {
		extensions: ['', '.js', '.jsx'],
	},
	plugins: [
		new webpack.DefinePlugin({'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development')}),
		new webpack.optimize.UglifyJsPlugin()
	],
};
