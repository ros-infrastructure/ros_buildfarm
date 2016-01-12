from pep8 import StyleGuide
import os


def test_pep8_conformance():
    """Test source code for PEP8 conformance."""
    pep8style = StyleGuide(max_line_length=100)
    report = pep8style.options.report
    report.start()
    base_path = os.path.join(os.path.dirname(__file__), '..')
    pep8style.input_dir(os.path.join(base_path, 'ros_buildfarm'))
    pep8style.input_dir(os.path.join(base_path, 'scripts'))
    report.stop()
    assert report.total_errors == 0, \
        'Found %d code style errors (and warnings)' % report.total_errors


if __name__ == '__main__':
    test_pep8_conformance()
