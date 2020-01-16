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

try:
    # while this is not supposed to be done I don't see a different way atm
    reload(sys)
    sys.setdefaultencoding('utf-8')
except NameError:
    pass

from ros_buildfarm.argument import add_argument_build_name  # noqa
from ros_buildfarm.argument import add_argument_cache_dir  # noqa
from ros_buildfarm.argument import add_argument_config_url  # noqa
from ros_buildfarm.argument import add_argument_output_dir  # noqa
from ros_buildfarm.argument import add_argument_rosdistro_name  # noqa
from ros_buildfarm.status_page import build_release_status_page  # noqa


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Generate the release status page')
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'release')
    add_argument_cache_dir(parser, '/tmp/package_repo_cache')
    add_argument_output_dir(parser)
    parser.add_argument(
        '--copy-resources',
        action='store_true',
        help='Copy the resources instead of using symlinks')
    args = parser.parse_args(argv)

    return build_release_status_page(
        args.config_url, args.rosdistro_name, args.release_build_name,
        args.cache_dir, args.output_dir, copy_resources=args.copy_resources)


if __name__ == '__main__':
    main()
