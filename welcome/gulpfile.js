var gulp = require('gulp');
var babel = require("gulp-babel");
var requirejsOptimize = require('gulp-requirejs-optimize');

gulp.task('default', ['scripts'], function() {
});

gulp.task('jsx', function () {
	return gulp.src('src/welcome/app/**/*.jsx')
		.pipe(babel({
			presets: ['es2015', 'stage-0', 'react']
		}))
		.pipe(gulp.dest('src/welcome/build'));
});

gulp.task('js', function () {
	return gulp.src('src/welcome/app/**/*.js')
		.pipe(gulp.dest('src/welcome/build'));
});

gulp.task('scripts', ['jsx', 'js'], function () {
	return gulp.src('src/welcome/build/welcome/welcome.js')
		.pipe(requirejsOptimize({
			//optimize: 'none',
			paths: {
				'react': 'empty:',
				'react-mdl': 'empty:',
				'react-router': 'empty:'
			},
			baseUrl: 'src/welcome/build',
			name: 'welcome/welcome'
		}))
		.pipe(gulp.dest('src/welcome/htdocs'));
});

gulp.task('watch', ['default'], function() {
	gulp.watch('src/welcome/app/**/*.jsx', ['default']);
});
