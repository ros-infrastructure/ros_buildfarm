#!/usr/bin/env python3

# Copyright 2020 Open Source Robotics Foundation, Inc.
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

from ros_buildfarm.argument import add_argument_dry_run
from ros_buildfarm.argument import add_argument_invalidate
from ros_buildfarm.argument import add_argument_pulp_base_url
from ros_buildfarm.argument import add_argument_pulp_distribution_name
from ros_buildfarm.argument import add_argument_pulp_password
from ros_buildfarm.argument import add_argument_pulp_task_timeout
from ros_buildfarm.argument import add_argument_pulp_username
from ros_buildfarm.common import Scope
from ros_buildfarm.pulp import format_pkg_ver
from ros_buildfarm.pulp import PulpRpmClient


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Import packages into a repository and publish it')
    parser.add_argument(
        'package_resources',
        nargs='*', metavar="PULP_HREF",
        help='Identifiers for packages which should be imported')
    add_argument_dry_run(parser)
    add_argument_invalidate(parser)
    parser.add_argument(
        '--invalidate-expression',
        default=None,
        help='Any existing package names matching this expression will be removed')
    add_argument_pulp_base_url(parser)
    add_argument_pulp_distribution_name(parser)
    add_argument_pulp_password(parser)
    add_argument_pulp_task_timeout(parser)
    add_argument_pulp_username(parser)
    args = parser.parse_args(argv)

    pulp_client = PulpRpmClient(
        args.pulp_base_url, args.pulp_username, args.pulp_password,
        task_timeout=args.pulp_task_timeout)

    with Scope('SUBSECTION', 'performing repository transaction'):
        pkgs_added, pkgs_removed = pulp_client.import_and_invalidate(
            args.pulp_distribution_name, args.package_resources,
            args.invalidate_expression, args.invalidate, dry_run=args.dry_run)

    with Scope('SUBSECTION', 'enumerating results'):
        if not pkgs_added:
            print('Not importing any new packages')
        for pkg in pkgs_added:
            print('Importing package: %s-%s.%s' % (pkg.name, format_pkg_ver(pkg), pkg.arch))

        if not pkgs_removed:
            print('Not removing any existing packages')
        for pkg in pkgs_removed:
            print('Removing package: %s-%s.%s' % (pkg.name, format_pkg_ver(pkg), pkg.arch))


if __name__ == '__main__':
    sys.exit(main())
