from em import Interpreter
from io import StringIO
import os
from xml.sax.saxutils import escape

template_basepath = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'templates'))


def expand_template(template_name, data):
    output = StringIO()
    try:
        interpreter = Interpreter(output=output)
        template_path = os.path.join(template_basepath, template_name)
        escaped_data = {}
        for k, v in data.items():
            if k.startswith('-'):
                k = k[1:]
            else:
                v = escape_value(v)
            escaped_data[k] = v
        interpreter.file(open(template_path), locals=escaped_data)
        return output.getvalue()
    finally:
        interpreter.shutdown()


def escape_value(value):
    if isinstance(value, list):
        value = [escape_value(v) for v in value]
    elif isinstance(value, set):
        value = set([escape_value(v) for v in value])
    elif isinstance(value, str):
        value = escape(value)
    return value


def get_scm_snippet(repo_spec, path=None):
    assert repo_spec.type in ['git', 'hg', 'svn']

    if repo_spec.type == 'git':
        data = {
            'url': repo_spec.url,
            'refspec': repo_spec.version,
        }
        if path is not None:
            data['relative_target_dir'] = path
        return expand_template('snippet/scm_git.xml.em', data)

    if repo_spec.type == 'hg':
        data = {
            'source': repo_spec.url,
            'branch': repo_spec.version,
        }
        if path is not None:
            data['subdir'] = path
        return expand_template('snippet/scm_hg.xml.em', data)

    if repo_spec.type == 'svn':
        data = {
            'remote': repo_spec.url,
        }
        if path is not None:
            data['local'] = path
        return expand_template('snippet/scm_svn.xml.em', data)

    assert False
