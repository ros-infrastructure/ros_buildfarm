#!/usr/bin/env python3

# Copyright 2014, 2016, 2020 Open Source Robotics Foundation, Inc.
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

import argparse
import sys

from ros_buildfarm.argument import add_argument_package_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_skip_download_sourcepkg
from ros_buildfarm.argument import add_argument_sourcepkg_dir
from ros_buildfarm.binaryrpm_job import get_sourcerpm
from ros_buildfarm.common import Scope


def main(argv=sys.argv[1:]):
    with Scope('SUBSECTION', 'get sourcerpm'):
        parser = argparse.ArgumentParser(
            description='Get released package sourcerpm')
        add_argument_rosdistro_index_url(parser)
        add_argument_rosdistro_name(parser)
        add_argument_package_name(parser)
        add_argument_sourcepkg_dir(parser)
        add_argument_skip_download_sourcepkg(parser)
        args = parser.parse_args(argv)

        return get_sourcerpm(
            args.rosdistro_index_url, args.rosdistro_name, args.package_name,
            args.sourcepkg_dir, args.skip_download_sourcepkg)


if __name__ == '__main__':
    sys.exit(main())
