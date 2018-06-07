
Hello world plugin
##################

Before making any plugin we have to create a setup file for the plugin.
For more about `setup.py <http://tellstick-server.readthedocs.io/en/latest/python/anatomy.html>`_.

Add following code in setup.py :

::


  try:
    from setuptools import setup
    from setuptools.command.install import install
  except ImportError:
    from distutils.core import setup
    from distutils.command.install import install
  import os

  class buildweb(install):
    def run(self):
      print("generate web application")
      os.system('npm install')
      os.system('npm run build')
      install.run(self)

  setup(
    name='Welcome',
    version='0.1',
    packages=['welcome'],
    package_dir = {'':'src'},
    cmdclass={'install': buildweb},  #Call the fuction buildweb
    entry_points={ \
    'telldus.plugins': ['c = welcome:Welcome [cREQ]']
    },
    extras_require = dict(cREQ = 'Base>=0.1\nTelldus>=0.1\nTelldusWeb>=0.1')
  )



Now create plugin file :

For Interacting with UI import interface ``IWebReactHandler`` from ``telldus.web``
and implements it into the plugin.

::


  from base import Plugin, implements 
  from telldus.web import IWebReactHandler

  class Welcome(Plugin):
    implements(IWebReactHandler)

    @staticmethod
    def getReactComponents():
    return {
      'welcome': {
      'title': 'Welcome',
      'script': 'welcome/welcome.js',
      'tags': ['menu'],
    }
  }

Here, the function ``getReactComponents()`` Return a list of components this plugin exports.



Hello world plugin UI
#####################


Run ``npm init`` command in the root folder, It will ask for the package details and fill it out.

It will create a package.json file in your root folder.

Cofigur package.json
====================

Make following modifications in the package.json file.

::


  {
    "name": "welcome",
    "version": "1.0.0",
    "scripts": {
      "build": "gulp",
      "watch": "gulp watch"
    },
    "devDependencies": {
      "babel-cli": "^6.18.0",
      "babel-preset-es2015": "^6.16.0",
      "babel-preset-react": "^6.16.0",
      "babel-preset-stage-0": "^6.16.0",
      "gulp": "^3.9.1",
      "gulp-babel": "^6.1.2",
      "gulp-cli": "^1.2.2",
      "gulp-requirejs-optimize": "^1.2.0",
      "requirejs": "^2.3.2"
    }
  }


That are major dependencies to run and display UI.


Create gulpfile
===============

Now create gulpfile.js in the root folder.

Gulp is a toolkit for automating painful or time-consuming tasks in your development workflow, so you can stop messing around and build something. `more <https://gulpjs.com/>`_

Add following task in gulpfile:

::

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

Here, 
gulp task ``jsx`` will copy all file from the specified path and convert it and paste it into the destination path.

gulp task ``js`` and ``script`` will do same as ``jsx``.


Create UI design
================


Now Design UI using `react <https://reactjs.org/>`_ and give extension ``.jsx`` and save this file to the path that you have given in gulpfile.

::

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
    }
  );

Now the plugin is ready to install and use.
