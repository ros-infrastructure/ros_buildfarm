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
import re
import sys

from ros_buildfarm.argument import add_argument_pulp_base_url
from ros_buildfarm.argument import add_argument_pulp_distribution_name
from ros_buildfarm.argument import add_argument_pulp_password
from ros_buildfarm.argument import add_argument_pulp_resource_record
from ros_buildfarm.argument import add_argument_pulp_task_timeout
from ros_buildfarm.argument import add_argument_pulp_username
from ros_buildfarm.common import Scope
from ros_buildfarm.pulp import format_pkg_ver
from ros_buildfarm.pulp import PulpRpmClient


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='List the pulp IDs of packages provided at a given pulp distribution endpoint')
    add_argument_pulp_base_url(parser)
    add_argument_pulp_distribution_name(parser)
    add_argument_pulp_password(parser)
    add_argument_pulp_resource_record(parser)
    add_argument_pulp_task_timeout(parser)
    add_argument_pulp_username(parser)
    parser.add_argument(
        '--package-name-expression', default=None,
        help='Expression to match against packages in the repository')
    args = parser.parse_args(argv)

    pulp_client = PulpRpmClient(
        args.pulp_base_url, args.pulp_username, args.pulp_password,
        task_timeout=args.pulp_task_timeout)

    with Scope('SUBSECTION', 'list packages in the distribution'):
        pkgs = pulp_client.enumerate_pkgs_in_distribution_name(args.pulp_distribution_name)

        print('Total packages in repository: %d' % len(pkgs))

        if args.package_name_expression:
            compiled_expression = re.compile(args.package_name_expression)
            pkgs = [pkg for pkg in pkgs if compiled_expression.match(pkg.name)]

        pkgs = sorted(pkgs, key=lambda pkg: pkg.name)

        print('Found %d packages:' % len(pkgs))
        for pkg in pkgs:
            print('- %s-%s' % (pkg.name, format_pkg_ver(pkg)))

        if args.pulp_resource_record:
            print("Saving pulp resource record to '%s'." % args.pulp_resource_record)
            with open(args.pulp_resource_record, 'w') as resource_record:
                resource_record.write('PULP_RESOURCES=%s\n' % (
                    ' '.join([pkg.pulp_href for pkg in pkgs])))


if __name__ == '__main__':
    sys.exit(main())
