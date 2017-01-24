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
import sys

from pyflakes.api import checkRecursive
from pyflakes.reporter import Reporter


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
