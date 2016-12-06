var gulp = require('gulp');
var babel = require("gulp-babel");
var requirejsOptimize = require('gulp-requirejs-optimize');

gulp.task('default', ['main', 'auth'], function() {
});

gulp.task('jsx', function () {
	return gulp.src('src/api/app/**/*.jsx')
		.pipe(babel({
			presets: ['es2015', 'stage-0', 'react']
		}))
		.pipe(gulp.dest('src/api/build'));
});

gulp.task('js', function () {
	return gulp.src('src/api/app/**/*.js')
		.pipe(gulp.dest('src/api/build'));
});

gulp.task('main', ['jsx', 'js'], function () {
	return gulp.src('src/api/build/api/api.js')
		.pipe(requirejsOptimize({
			paths: {
				'react': 'empty:',
				'react-mdl': 'empty:',
				'react-redux': 'empty:',
				'react-router': 'empty:',
				'dialog-polyfill': 'empty:',
				'telldus': 'empty:',
				'websocket': 'empty:'
			},
			baseUrl: 'src/api/build',
			name: 'api/api'
		}))
		.pipe(gulp.dest('src/api/htdocs'));
});

gulp.task('auth', ['jsx', 'js'], function () {
	return gulp.src('src/api/build/api/authorize.js')
		.pipe(requirejsOptimize({
			paths: {
				'react': 'empty:',
				'react-mdl': 'empty:',
			},
			baseUrl: 'src/api/build',
			name: 'api/authorize'
		}))
		.pipe(gulp.dest('src/api/htdocs'));
});

gulp.task('watch', ['default'], function() {
	gulp.watch('src/api/app/**/*.jsx', ['default']);
});
