module.exports = function(grunt) {
    grunt.initConfig({
        nunjucks: {
            precompile: {
                baseDir: 'kitsune/sumo/static',
                src: 'kitsune/sumo/static/tpl/*',
                dest: 'kitsune/sumo/static/js/nunjucks-templates.js'
            }
        },
        watch: {
            nunjucks: {
                files: 'kitsune/sumo/static/tpl/*',
                tasks: ['nunjucks']
            }
        }
    });

    grunt.loadNpmTasks('grunt-nunjucks');
    grunt.loadNpmTasks('grunt-contrib-watch');

    grunt.registerTask('default', ['watch']);
}
