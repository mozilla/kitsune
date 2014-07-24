var gulp = require('gulp');
var nunjucks = require('gulp-nunjucks');
var watch = require('gulp-watch');

gulp.task('nunjucks', function() {
    return gulp.src('kitsune/sumo/static/tpl/*')
        .pipe(nunjucks())
        .pipe(gulp.dest('kitsune/sumo/static/js/templates'));
});

gulp.task('watch', ['nunjucks'], function() {
    return gulp.watch('kitsune/sumo/static/tpl/*', ['nunjucks']);
});

gulp.task('default', ['watch']);
