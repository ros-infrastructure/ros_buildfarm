from __future__ import print_function

from em import Interpreter
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import os
import pkg_resources
import shutil
import stat
import sys
import time
from xml.sax.saxutils import escape

interpreter = None
template_hooks = None


def expand_template(template_name, data, options=None):
    """Return expanded template as a string."""

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

        with open(template_path, 'r') as fh:
            interpreter.file(fh, locals=data)
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
    """Add interpreter helper functions."""
    data['ESCAPE'] = _escape_value
    data['SNIPPET'] = _expand_snippet
    data['TEMPLATE'] = _expand_template


def _escape_value(value):
    """Return escape value respective of input isinstance type."""
    if isinstance(value, list):
        value = [_escape_value(v) for v in value]
    elif isinstance(value, set):
        value = set([_escape_value(v) for v in value])
    elif isinstance(value, str):
        value = escape(value)
    return value


def _expand_snippet(snippet_name, **kwargs):
    """Extract template name from snippet name and expand template."""
    template_name = 'snippet/%s.xml.em' % snippet_name
    _expand_template(template_name, **kwargs)


def _expand_template(template_name, **kwargs):
    """Open template and apply interpreter."""
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
    """Return first found template resource respective to template_packages order."""
    if 'template_packages' not in kwargs:
        # Default to ros_buildfarm if none given
        return 'ros_buildfarm'

    # Look through each given template package
    for template_package in kwargs['template_packages']:
        if pkg_resources.resource_exists(template_package, template_name):
            return template_package

    # Default to ros_buildfarm if none found
    return 'ros_buildfarm'


def _find_first_wrappers(**data):
    """Return first found wrappers resource respective to template_packages order."""
    wrapper_scripts = {}
    wrapper_subpath = 'templates/wrapper'
    for template_package in data['template_packages']:
        if pkg_resources.resource_exists(template_package, wrapper_subpath):
            wrapper_path = pkg_resources.resource_filename(template_package, wrapper_subpath)
            wrapper_files = pkg_resources.resource_listdir(template_package, wrapper_subpath)
            for filename in wrapper_files:
                if not filename.endswith('.py'):
                    continue
                if filename in wrapper_scripts:
                    continue
                abs_file_path = os.path.join(wrapper_path, filename)
                with open(abs_file_path, 'r') as h:
                    content = h.read()
                    wrapper_scripts[filename] = content
    return wrapper_scripts


def create_dockerfile(data):
    """Write Dockerfile to disk using data and template."""

    # Create copy of data
    data = dict(data)

    # Prepend templates folder to name
    data['template_name'] = os.path.join('templates',  data['template_name'])

    template_name = data['template_name']
    dockerfile_dir = data['dockerfile_dir']

    # Find first instance of tempate_name given order of template_packages
    template_package = _find_first_template(**data)
    template_path = pkg_resources.resource_filename(template_package, template_name)
    data['template_path'] = template_path

    # Find first instance of wrapper_scripts given order of template_packages
    data['wrapper_scripts'] = _find_first_wrappers(**data)

    # Use wrapper scripts to expand template
    content = expand_template(template_name, data)

    # Print and save content to Dockerfile
    dockerfile = os.path.join(dockerfile_dir, 'Dockerfile')
    print("Generating Dockerfile '%s':" % dockerfile)
    # for line in content.splitlines():
    #     print(' ', line)
    with open(dockerfile, 'w') as h:
        h.write(content)

    # Add entrypoint script
    if 'entrypoint_name' in data:
        entrypoint_data = dict(data)
        entrypoint_data['entrypoint_name'] = os.path.join('templates',
                                                          entrypoint_data['entrypoint_name'])
        entrypoint_data['template_name'] = entrypoint_data['entrypoint_name']
        entrypoint_package = _find_first_template(**entrypoint_data)
        entrypoint_path = pkg_resources.resource_filename(entrypoint_package,
                                                          entrypoint_data['entrypoint_name'])
        # copy script into dockerfile_dir
        entrypoint_dest = os.path.join(dockerfile_dir, os.path.basename(entrypoint_path))
        shutil.copyfile(entrypoint_path, entrypoint_dest)

        # make script executable
        st = os.stat(entrypoint_dest)
        os.chmod(entrypoint_dest, st.st_mode | stat.S_IEXEC)
