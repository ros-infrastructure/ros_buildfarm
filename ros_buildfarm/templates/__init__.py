from __future__ import print_function

from em import Interpreter
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import os
import sys
import time
from xml.sax.saxutils import escape

template_basepath = os.path.abspath(os.path.dirname(__file__))

interpreter = None
template_hooks = None


def expand_template(template_name, data, options=None):
    global template_basepath
    global interpreter
    global template_hooks

    output = StringIO()
    try:
        interpreter = Interpreter(output=output, options=options)
        for template_hook in template_hooks or []:
            interpreter.addHook(template_hook)
        template_path = os.path.join(template_basepath, template_name)
        # create copy before manipulating
        data = dict(data)
        # add some generic information to context
        data['template_name'] = template_name
        now = time.localtime()
        data['now_str'] = time.strftime(
            '%Y-%m-%d %H:%M:%S %z', now)
        data['today_str'] = time.strftime(
            '%Y-%m-%d (%z)', now)
        tz_name = time.strftime('%Z', now)
        tz_offset = time.strftime('%z', now)
        data['timezone'] = '%s%s%s' % \
            (tz_name, '+' if tz_offset[0] == '-' else '-', tz_offset[1:3])

        _add_helper_functions(data)

        interpreter.file(open(template_path, 'r'), locals=data)
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
    data['ESCAPE'] = _escape_value
    data['SNIPPET'] = _expand_snippet
    data['TEMPLATE'] = _expand_template


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
    global template_basepath
    global interpreter
    template_path = os.path.join(template_basepath, template_name)
    _add_helper_functions(kwargs)
    with open(template_path, 'r') as h:
        try:
            interpreter.include(h, kwargs)
        except Exception as e:
            print(
                "%s in template '%s': %s" %
                (e.__class__.__name__, template_name, str(e)), file=sys.stderr)
            sys.exit(1)


def create_dockerfile(template_name, data, dockerfile_dir):
    data['template_name'] = template_name

    wrapper_scripts = {}
    wrapper_script_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'scripts', 'wrapper')
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
