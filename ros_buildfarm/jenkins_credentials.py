# Copyright 2014-2015 Open Source Robotics Foundation, Inc.
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

from __future__ import print_function

from configparser import ConfigParser
import os
import sys


def get_credentials(jenkins_url=None):
    config = ConfigParser()
    config_file = get_credential_path()
    if not os.path.exists(config_file):
        print("Could not find credential file '%s'" % config_file,
              file=sys.stderr)
        return None, None

    config.read(config_file)
    section_name = None
    if jenkins_url is not None and jenkins_url in config:
        section_name = jenkins_url
    if section_name is None and 'DEFAULT' in config:
        section_name = 'DEFAULT'

    if section_name is None or 'username' not in config[section_name] or \
            'password' not in config[section_name]:
        print(
            "Could not find credentials for '%s' in file '%s'" %
            (jenkins_url, config_file), file=sys.stderr)
        return None, None
    return config[section_name]['username'], config[section_name]['password']


def get_credential_path():
    return os.path.join(
        os.path.expanduser('~'), get_relative_credential_path())


def get_relative_credential_path():
    return os.path.join('.buildfarm', 'jenkins.ini')
