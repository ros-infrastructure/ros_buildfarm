#!/usr/bin/env python3

# Copyright 2014 Open Source Robotics Foundation, Inc.
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

from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_source_dir
from ros_buildfarm.common import Scope
from ros_buildfarm.sourcedeb_job import build_sourcedeb


def main(argv=sys.argv[1:]):
    with Scope('SUBSECTION', 'build sourcedeb'):
        parser = argparse.ArgumentParser(
            description='Build package sourcedeb')
        add_argument_os_name(parser)
        add_argument_os_code_name(parser)
        add_argument_source_dir(parser)
        args = parser.parse_args(argv)

        return build_sourcedeb(
            args.source_dir,
            os_name=args.os_name, os_code_name=args.os_code_name)


if __name__ == '__main__':
    sys.exit(main())
