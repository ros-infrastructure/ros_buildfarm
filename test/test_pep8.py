# Copyright 2016 Open Source Robotics Foundation, Inc.
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

import os

from pep8 import StyleGuide


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
