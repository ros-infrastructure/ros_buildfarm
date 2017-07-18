# Copyright 2015-2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import os
import sys
import time
from xml.sax.saxutils import escape

from em import Interpreter

template_prefix_path = [os.path.abspath(os.path.dirname(__file__))]

interpreter = None
template_hooks = None


def get_template_path(template_name):
    global template_prefix_path
    for basepath in template_prefix_path:
        template_path = os.path.join(basepath, template_name)
        if os.path.exists(template_path):
            return template_path
    raise RuntimeError("Failed to find template '%s'" % template_name)


cached_tokens = {}


class CachingInterpreter(Interpreter):

    def parse(self, scanner, locals=None):
        global cached_tokens
        data = scanner.buffer
        # try to use cached tokens
        tokens = cached_tokens.get(data)
        if tokens is None:
            # collect tokens and cache them
            tokens = []
            while True:
                token = scanner.one()
                if token is None:
                    break
                tokens.append(token)
            cached_tokens[data] = tokens

        # reimplement the parse method using the (cached) tokens
        self.invoke('atParse', scanner=scanner, locals=locals)
        for token in tokens:
            self.invoke('atToken', token=token)
            token.run(self, locals)


def expand_template(template_name, data, options=None):
    global interpreter
    global template_hooks

    output = StringIO()
    try:
        interpreter = CachingInterpreter(output=output, options=options)
        for template_hook in template_hooks or []:
            interpreter.addHook(template_hook)
        template_path = get_template_path(template_name)
        # create copy before manipulating
        data = dict(data)
        # add some generic information to context
        data['template_name'] = template_name
        now = time.localtime()
        data['now_str'] = time.strftime(
            '%Y-%m-%d %H:%M:%S %z', now)
        data['today_str'] = time.strftime(
            '%Y-%m-%d (%z)', now)
        data['timezone'] = '%s%s%02d' % (
            time.tzname[0], '-' if time.timezone < 0 else '+',
            time.timezone / 60 / 60)
        data['wrapper_scripts'] = get_wrapper_scripts()

        _add_helper_functions(data)

        with open(template_path, 'r') as h:
            content = h.read()
            interpreter.invoke(
                'beforeFile', name=template_name, file=h, locals=data)
        interpreter.string(content, template_path, locals=data)
        interpreter.invoke('afterFile')

        value = output.getvalue()
        return value
    except Exception as e:
        print("%s processing template '%s'" %
              (e.__class__.__name__, template_name), file=sys.stderr)
        raise
    finally:
        interpreter.shutdown()
        interpreter = None


def _add_helper_functions(data):
    data['FILE'] = _get_file_content
    data['ESCAPE'] = _escape_value
    data['SNIPPET'] = _expand_snippet
    data['TEMPLATE'] = _expand_template


def _get_file_content(filename):
    path = get_template_path(filename)
    with open(path, 'r') as h:
        return h.read()


def _escape_value(value):
    if isinstance(value, list):
        value = [_escape_value(v) for v in value]
    elif isinstance(value, set):
        value = set([_escape_value(v) for v in value])
    elif isinstance(value, str):
        value = escape(value)
    return value


def _expand_snippet(snippet_name, **kwargs):
    template_name = 'snippet/%s.xml.em' % snippet_name
    _expand_template(template_name, **kwargs)


def _expand_template(template_name, **kwargs):
    global interpreter
    template_path = get_template_path(template_name)
    _add_helper_functions(kwargs)
    with open(template_path, 'r') as h:
        interpreter.invoke('beforeInclude', name=template_path, file=h, locals=kwargs)
        content = h.read()
    try:
        interpreter.string(content, template_path, kwargs)
    except Exception as e:
        print(
            "%s in template '%s': %s" %
            (e.__class__.__name__, template_name, str(e)), file=sys.stderr)
        sys.exit(1)
    interpreter.invoke('afterInclude')


def create_dockerfile(template_name, data, dockerfile_dir, verbose=True):
    data['template_name'] = template_name
    data['wrapper_scripts'] = get_wrapper_scripts()
    content = expand_template(template_name, data)
    dockerfile = os.path.join(dockerfile_dir, 'Dockerfile')
    print("Generating Dockerfile '%s':" % dockerfile)
    if verbose:
        for line in content.splitlines():
            print(' ', line)
    with open(dockerfile, 'w') as h:
        h.write(content)


def get_wrapper_scripts():
    wrapper_scripts = {}
    for filename in ['apt.py', 'git.py']:
        wrapper_script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'wrapper')
        abs_file_path = os.path.join(
            wrapper_script_path, filename)
        with open(abs_file_path, 'r') as h:
            content = h.read()
            wrapper_scripts[filename] = content
    return wrapper_scripts
