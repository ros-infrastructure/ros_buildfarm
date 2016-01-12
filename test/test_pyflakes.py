from pyflakes.api import checkRecursive
from pyflakes.reporter import Reporter
import os
import sys


def test_pyflakes_conformance():
    """Test source code for PyFlakes conformance."""
    reporter = Reporter(sys.stdout, sys.stderr)
    base_path = os.path.join(os.path.dirname(__file__), '..')
    paths = [
        os.path.join(base_path, 'ros_buildfarm'),
        os.path.join(base_path, 'scripts'),
    ]
    warning_count = checkRecursive(paths, reporter)
    assert warning_count == 0, \
        'Found %d code style warnings' % warning_count


if __name__ == '__main__':
    test_pyflakes_conformance()
