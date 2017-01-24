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

from flake8.api.legacy import StyleGuide
from flake8.main.application import Application


def test_flake8_conformance():
    """Test source code for flake8 conformance."""
    argv = [
        '--ignore=%s' % ','.join([
            'D100', 'D101', 'D102', 'D103', 'D104', 'D105',
            'E501']),
        '--import-order-style=google',
    ]
    style_guide = get_style_guide(argv)
    base_path = os.path.join(os.path.dirname(__file__), '..')
    paths = [
        os.path.join(base_path, 'ros_buildfarm'),
        os.path.join(base_path, 'scripts'),
        os.path.join(base_path, 'test'),
    ]
    report = style_guide.check_files(paths)
    assert report.total_errors == 0, \
        'Found %d code style warnings' % report.total_errors


def get_style_guide(argv=None):
    # this is a fork of flake8.api.legacy.get_style_guide
    # to allow passing command line argument
    application = Application()
    application.find_plugins()
    application.register_plugin_options()
    application.parse_configuration_and_cli(argv)
    application.make_formatter()
    application.make_notifier()
    application.make_guide()
    application.make_file_checker_manager()
    return StyleGuide(application)


if __name__ == '__main__':
    test_flake8_conformance()
