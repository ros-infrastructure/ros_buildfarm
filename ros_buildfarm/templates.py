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
        # create copy before manipulating
        data = dict(data)
        data['ESCAPE'] = _escape_value
        data['SNIPPET'] = _expand_snippet
        interpreter.file(open(template_path), locals=data)
        return output.getvalue()
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
    return expand_template(template_name, kwargs)
