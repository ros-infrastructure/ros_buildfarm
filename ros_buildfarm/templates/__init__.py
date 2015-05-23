from __future__ import print_function

from em import Interpreter
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import os
import pkg_resources
import sys
import time
from xml.sax.saxutils import escape

interpreter = None
template_hooks = None


def expand_template(template_name, data, options=None):
    """Expand template call API"""

    global interpreter
    global template_hooks

    output = StringIO()
    try:
        interpreter = Interpreter(output=output, options=options)
        for template_hook in template_hooks or []:
            interpreter.addHook(template_hook)
        template_path = data['template_path']

        # create copy before manipulating
        data = dict(data)

        # add some generic information to context
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
    """Add helper functions to data dictionary"""
    data['ESCAPE'] = _escape_value
    data['SNIPPET'] = _expand_snippet
    data['TEMPLATE'] = _expand_template


def _escape_value(value):
    """Recusivly escape values of diffrent types"""
    if isinstance(value, list):
        value = [_escape_value(v) for v in value]
    elif isinstance(value, set):
        value = set([_escape_value(v) for v in value])
    elif isinstance(value, str):
        value = escape(value)
    return value


def _expand_snippet(snippet_name, **kwargs):
    """Expand snippet using given snippet_name"""
    template_name = 'snippet/%s.xml.em' % snippet_name
    _expand_template(template_name, **kwargs)


def _expand_template(template_name, **kwargs):
    """Expand template call for interpreter"""
    template_name = os.path.join('templates', template_name)
    template_package = _find_first_template(template_name, **kwargs)

    global interpreter
    template_path = pkg_resources.resource_filename(template_package, template_name)
    _add_helper_functions(kwargs)
    with open(template_path, 'r') as h:
        try:
            interpreter.include(h, kwargs)
        except Exception as e:
            print(
                "%s in template '%s': %s" %
                (e.__class__.__name__, template_name, str(e)), file=sys.stderr)
            sys.exit(1)

def _find_first_template(template_name, **kwargs):
    """Find first matching template resource given order of template_packages"""
    if not 'template_packages' in kwargs:
        # Default to ros_buildfarm if none given
        return 'ros_buildfarm'

    for template_package in kwargs['template_packages']:
        if pkg_resources.resource_exists(template_package,template_name):
            return template_package

    # Default to ros_buildfarm if none found
    return 'ros_buildfarm'

def _find_first_wrappers(data):
    """Find first wrappers resource given order of template_packages"""
    wrapper_scripts = {}
    wrapper_subpath = 'templates/wrapper'
    for template_package in data['template_packages']:
        if pkg_resources.resource_exists(template_package,wrapper_subpath):
            wrapper_path  = pkg_resources.resource_filename(template_package, wrapper_subpath)
            wrapper_files = pkg_resources.resource_listdir (template_package, wrapper_subpath)
            for filename in wrapper_files:
                if not filename.endswith('.py'):
                    continue
                if filename in wrapper_scripts:
                    continue
                abs_file_path = os.path.join(wrapper_path,filename)
                with open(abs_file_path, 'r') as h:
                    content = h.read()
                    wrapper_scripts[filename] = content
    return wrapper_scripts


def create_dockerfile(template_name, data, dockerfile_dir):
    """Create an auto generated docker file using given data config"""

    # template_names are relative to templates folder in template_packages
    template_name = os.path.join('templates', template_name)

    # Find first instance of tempate_name given order of template_packages
    template_package  = _find_first_template(template_name, **data)
    template_path     = pkg_resources.resource_filename(template_package, template_name)
    data['template_name'] = template_name
    data['template_path'] = template_path

    # Find first instance of wrapper_scripts given order of template_packages
    data['wrapper_scripts'] = _find_first_wrappers(data)

    # Use wrapper scripts to expand template
    content = expand_template(template_name, data)

    # Print and save content to Dockerfile
    dockerfile = os.path.join(dockerfile_dir, 'Dockerfile')
    print("Generating Dockerfile '%s':" % dockerfile)
    for line in content.splitlines():
        print(' ', line)
    with open(dockerfile, 'w') as h:
        h.write(content)
