import re

from django.conf import settings
from django.utils.encoding import smart_bytes

from pipeline.compilers import CompilerBase
from pipeline.exceptions import CompilerError


class BrowserifyCompiler(CompilerBase):
    output_extension = 'browserified.js'

    def match_file(self, path):
        # Allow for cache busting hashes between ".browserify" and ".js"
        return re.search(r'\.browserify(\.[a-fA-F0-9]+)?\.js$', path) is not None

    def compile_file(self, infile, outfile, outdated=False, force=False):
        pipeline_settings = getattr(settings, 'PIPELINE', {})
        command = "%s %s %s > %s" % (
            pipeline_settings.get('BROWSERIFY_BINARY', '/usr/bin/env browserify'),
            pipeline_settings.get('BROWSERIFY_ARGUMENTS', ''),
            infile,
            outfile
        )
        return self.execute_command(command)

    def execute_command(self, command, content=None, cwd=None):
        """This is like the one in SubProcessCompiler, except it checks the exit code."""
        import subprocess
        pipe = subprocess.Popen(command, shell=True, cwd=cwd,
                                stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        if content:
            content = smart_bytes(content)
        stdout, stderr = pipe.communicate(content)
        if self.verbose:
            print(stderr)
        if pipe.returncode != 0:
            raise CompilerError(stderr)
        return stdout
