from __future__ import print_function

from em import Error
from em import Interpreter
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import os
import sys
import time
from xml.sax.saxutils import escape

template_basepath = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'templates'))


system_timezone = None
template_hook = None


def expand_template(
        template_name, data, options=None, add_context_variables=True):
    global system_timezone
    global template_hook

    if system_timezone is None and add_context_variables:
        if 'TZ' in os.environ:
            system_timezone = os.environ['TZ']
        else:
            with open('/etc/timezone', 'r') as h:
                system_timezone = h.read().strip()

    output = StringIO()
    try:
        interpreter = Interpreter(output=output, options=options)
        template_path = os.path.join(template_basepath, template_name)
        # create copy before manipulating
        data = dict(data)
        if add_context_variables:
            data['template_name'] = template_name
            now = time.localtime()
            data['now_str'] = time.strftime(
                '%Y-%m-%d %H:%M:%S %z', now)
            data['today_str'] = time.strftime(
                '%Y-%m-%d (%z)', now)
            data['timezone'] = system_timezone
        data['ESCAPE'] = _escape_value
        data['TEMPLATE'] = _expand_template
        data['SNIPPET'] = _expand_snippet
        interpreter.file(open(template_path, 'r'), locals=data)
        value = output.getvalue()
        if template_hook:
            template_hook(template_name, data, value)
        return value
    except Exception as e:
        print("%s processing template '%s'" %
              (e.__class__.__name__, template_name), file=sys.stderr)
        raise
    finally:
        interpreter.shutdown()


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
    return _expand_template(template_name, **kwargs)


def _expand_template(template_name, **kwargs):
    try:
        value = expand_template(
            template_name, kwargs, add_context_variables=False)
        return value
    except Error as e:
        print("%s in template '%s': %s" %
              (e.__class__.__name__, template_name, str(e)), file=sys.stderr)
        sys.exit(1)


def create_dockerfile(template_name, data, dockerfile_dir):
    data['template_name'] = template_name

    wrapper_scripts = {}
    wrapper_script_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'scripts', 'wrapper')
    for filename in os.listdir(wrapper_script_path):
        if not filename.endswith('.py'):
            continue
        abs_file_path = os.path.join(wrapper_script_path, filename)
        with open(abs_file_path, 'r') as h:
            content = h.read()
            wrapper_scripts[filename] = content
    data['wrapper_scripts'] = wrapper_scripts

    content = expand_template(template_name, data)
    dockerfile = os.path.join(dockerfile_dir, 'Dockerfile')
    print("Generating Dockerfile '%s':" % dockerfile)
    for line in content.splitlines():
        print(' ', line)
    with open(dockerfile, 'w') as h:
        h.write(content)
