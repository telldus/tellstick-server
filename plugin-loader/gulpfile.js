var gulp = require('gulp');
var babel = require("gulp-babel");
var requirejsOptimize = require('gulp-requirejs-optimize');


gulp.task('babel', function () {
	return gulp.src(['src/pluginloader/app/**/*.jsx', 'src/pluginloader/app/**/*.js'])
		.pipe(babel({
			presets: ['es2015', 'stage-0', 'react']
		}))
		.pipe(gulp.dest('src/pluginloader/build'));
});

gulp.task('oauth2', gulp.series('babel', function () {
	return gulp.src('src/pluginloader/build/plugins/oauth2.js')
		.pipe(requirejsOptimize({
			//optimize: 'none',
			paths: {
				'react': 'empty:',
				'react-mdl': 'empty:',
			},
			baseUrl: 'src/pluginloader/build',
			name: 'plugins/oauth2'
		}))
		.pipe(gulp.dest('src/pluginloader/htdocs'));
}));


gulp.task('plugins', gulp.series('babel', function () {
	return gulp.src('src/pluginloader/build/plugins/plugins.js')
		.pipe(requirejsOptimize({
			//optimize: 'none',
			paths: {
				'react': 'empty:',
				'react-markdown': 'empty:',
				'react-mdl': 'empty:',
				'react-redux': 'empty:',
				'dialog-polyfill': 'empty:',
				'telldus': 'empty:',
				'websocket': 'empty:',
			},
			baseUrl: 'src/pluginloader/build',
			name: 'plugins/plugins'
		}))
		.pipe(gulp.dest('src/pluginloader/htdocs'));
}));



gulp.task('default', gulp.parallel('plugins', 'oauth2'));


gulp.task('watch', gulp.series('default', function() {
	gulp.watch(['src/pluginloader/app/**/*.jsx', 'src/pluginloader/app/**/*.js'], ['default']);
}));
