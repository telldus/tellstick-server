var webpack = require('webpack');
var path = require('path');

module.exports = {
	entry: {
		main: path.resolve(__dirname, 'src/telldus/app/main'),
		common: ['webpack-material-design-icons', 'whatwg-fetch'],
	},
	output: {
		path: path.resolve(__dirname, 'src/telldus/htdocs'),
		publicPath: '/telldus/',
		filename: './js/[name].entry.js'
	},
	module: {
		rules: [
			{ test: /\.(js|jsx)$/, include: path.resolve(__dirname, 'src/telldus/app'), exclude: /node_modules/, use: 'babel-loader' },
			{ test: /\.css$/, use: ['style-loader', 'css-loader'] },
			{ test: /\.(jpe?g|png|gif|svg|eot|woff|ttf|svg|woff2)$/, loader: "file-loader?name=[name].[ext]" }
		]
	},
	resolve: {
		extensions: ['.js', '.jsx'],
	},
	plugins: [
		new webpack.optimize.CommonsChunkPlugin({name:'common', filename:'./js/[name].lib.js'})
// 		new webpack.HotModuleReplacementPlugin(),
	],

};
