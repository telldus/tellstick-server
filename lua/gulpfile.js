var gulp = require('gulp');
var babel = require("gulp-babel");
var requirejsOptimize = require('gulp-requirejs-optimize');

gulp.task('default', ['scripts'], function() {
});

gulp.task('jsx', function () {
	return gulp.src('src/lua/app/**/*.jsx')
		.pipe(babel({
			presets: ['es2015', 'stage-0', 'react']
		}))
		.pipe(gulp.dest('src/lua/build'));
});

gulp.task('js', function () {
	return gulp.src('src/lua/app/**/*.js')
		.pipe(gulp.dest('src/lua/build'));
});

gulp.task('scripts', ['jsx', 'js'], function () {
	return gulp.src('src/lua/build/lua/lua.js')
		.pipe(requirejsOptimize({
			//optimize: 'none',
			paths: {
				'react': 'empty:',
				'react-mdl': 'empty:',
				'react-redux': 'empty:',
				'react-router': 'empty:',
				'dialog-polyfill': 'empty:',
				'telldus': 'empty:',
				'websocket': 'empty:'
			},
			baseUrl: 'src/lua/build',
			name: 'lua/lua'
		}))
		.pipe(gulp.dest('src/lua/htdocs'));
});

gulp.task('watch', ['default'], function() {
	gulp.watch('src/lua/app/*.jsx', ['default']);
});
