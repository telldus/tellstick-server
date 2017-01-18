var gulp = require('gulp');
var babel = require("gulp-babel");
var requirejsOptimize = require('gulp-requirejs-optimize');

gulp.task('default', ['scripts'], function() {
});

gulp.task("babel", function () {
	return gulp.src(['src/pluginloader/app/**/*.jsx', 'src/pluginloader/app/**/*.js'])
		.pipe(babel({
			presets: ['es2015', 'stage-0', 'react']
		}))
		.pipe(gulp.dest('src/pluginloader/build'));
});

gulp.task('scripts', ['babel'], function () {
	return gulp.src('src/pluginloader/build/plugins/plugins.js')
		.pipe(requirejsOptimize({
			//optimize: 'none',
			paths: {
				'react': 'empty:',
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
});

gulp.task('watch', ['default'], function() {
	gulp.watch(['src/pluginloader/app/**/*.jsx', 'src/pluginloader/app/**/*.js'], ['default']);
});
