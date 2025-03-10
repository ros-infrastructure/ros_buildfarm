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
import warnings
from xml.sax.saxutils import escape

try:
    # Import bangpath option name from EmPy v3
    from em import BANGPATH_OPT
    BANGPATH_VALUE = False
except ImportError:
    # EmPy 4 does not define an import-able constant for the updated bangpath
    # option and inverts its meaning.
    BANGPATH_OPT = 'ignoreBangpaths'
    BANGPATH_VALUE = True

try:
    # EmPy v3
    from em import Hook
except ImportError:
    # EmPy v4
    from emlib import Hook as _Hook

    class Hook(_Hook):
        """Hook implementation with compatibility back to EmPy v3."""

        def beforeFileLines(self, file, locals, *args, **kwargs):
            return self.beforeFile(None, file, locals)

        def afterFileLines(self):
            return self.afterFile()

        def beforeFileChunks(self, file, bufferSize, locals, *args, **kwargs):
            return self.beforeFile(None, file, locals)

        def afterFileChunks(self):
            return self.afterFile()

        def beforeFileFull(self, file, locals, *args, **kwargs):
            return self.beforeFile(None, file, locals)

        def afterFileFull(self):
            return self.afterFile()

        def beforeFile(self, name, file, locals):
            pass

        def afterFile(self):
            pass


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
    """Interpreter for EmPy which caches parsed tokens."""

    class _CachingScannerDecorator:

        def __init__(self, decoree, cache):
            self.__dict__.update({
                '_cache': cache,
                '_decoree': decoree,
                '_idx': 0,
            })

        def __getattr__(self, name):
            return getattr(self.__dict__['_decoree'], name)

        def __setattr__(self, name, value):
            if name in self.__dict__:
                self.__dict__[name] = value
            else:
                setattr(self.__dict__['_decoree'], name, value)

        def one(self, *args, **kwargs):
            if self._idx < len(self._cache):
                token, count = self._cache[self._idx]
                self.advance(count)
                self.sync()
            else:
                count = len(self._decoree)
                token = self._decoree.one(*args, **kwargs)
                count -= len(self._decoree)
                self._cache.append((token, count))

            self._idx += 1
            return token

    def parse(self, scanner, *args, **kwargs):  # noqa: A002 D102
        cache = cached_tokens.setdefault(scanner.buffer, [])
        return super().parse(
            CachingInterpreter._CachingScannerDecorator(scanner, cache),
            *args,
            **kwargs)


def expand_template(
    template_name, data, options=None, *, ignore_bangpath=None,
):
    global interpreter
    global template_hooks

    if options is not None:
        warnings.warn(
            "The 'options' argument is deprecated",
            category=DeprecationWarning,
            stacklevel=2)

    if ignore_bangpath:
        options = {
            **(options or {}),
            BANGPATH_OPT: BANGPATH_VALUE,
        }

    template_path = get_template_path(template_name)

    output = StringIO()
    try:
        from em import Configuration
    except ImportError:
        interpreter = CachingInterpreter(output=output, options=options)
    else:
        interpreter = CachingInterpreter(
            output=output,
            config=Configuration(
                **(options or {}),
                defaultRoot=str(template_path)),
            dispatcher=False)
    try:
        for template_hook in template_hooks or []:
            interpreter.addHook(template_hook)
        # create copy before manipulating
        data = dict(data)
        # add some generic information to context
        data['template_name'] = template_name
        now = time.localtime()
        data['now_str'] = time.strftime(
            '%Y-%m-%d %H:%M:%S %z', now)
        data['today_str'] = time.strftime(
            '%Y-%m-%d (%z)', now)
        data['timezone'] = '%s%+03d' % (
            time.tzname[0], time.timezone / 60 / 60)

        data['wrapper_scripts'] = get_wrapper_scripts()

        _add_helper_functions(data)

        with open(template_path, 'r') as h:
            content = h.read()
            interpreter.invoke(
                'beforeFile', name=template_name, file=h, locals=data)
        interpreter.string(content, locals=data)
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
        interpreter.string(content, locals=kwargs)
    except Exception as e:
        print(
            "%s in template '%s': %s" %
            (e.__class__.__name__, template_name, str(e)), file=sys.stderr)
        sys.exit(1)
    interpreter.invoke('afterInclude')


def create_dockerfile(template_name, data, dockerfile_dir, verbose=True):
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
