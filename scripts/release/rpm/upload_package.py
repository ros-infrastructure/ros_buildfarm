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

from ros_buildfarm.argument import add_argument_pulp_base_url
from ros_buildfarm.argument import add_argument_pulp_password
from ros_buildfarm.argument import add_argument_pulp_resource_record
from ros_buildfarm.argument import add_argument_pulp_task_timeout
from ros_buildfarm.argument import add_argument_pulp_username
from ros_buildfarm.common import Scope
from ros_buildfarm.pulp import format_pkg_ver
from ros_buildfarm.pulp import PulpRpmClient


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Upload package to pulp')
    parser.add_argument(
        'package_file',
        nargs='+', metavar='FILE',
        help='Package file paths to upload')
    add_argument_pulp_base_url(parser)
    add_argument_pulp_password(parser)
    add_argument_pulp_task_timeout(parser)
    add_argument_pulp_username(parser)
    add_argument_pulp_resource_record(parser)
    args = parser.parse_args(argv)

    pulp_client = PulpRpmClient(
        args.pulp_base_url, args.pulp_username, args.pulp_password,
        task_timeout=args.pulp_task_timeout)

    with Scope('SUBSECTION', 'upload package(s) to pulp'):
        created_resources = []

        for file_path in args.package_file:
            print("Uploading '%s'." % file_path)
            created_rpm = pulp_client.upload_pkg(file_path)
            created_resources.append(created_rpm.pulp_href)

            print('Created RPM resource: %s' % created_rpm.pulp_href)
            print("Package '%s' version: %s" % (created_rpm.name, format_pkg_ver(created_rpm)))

        if args.pulp_resource_record:
            print("Saving upload record to '%s'." % args.pulp_resource_record)
            with open(args.pulp_resource_record, 'w') as resource_record:
                resource_record.write('PULP_RESOURCES=%s\n' % ' '.join(created_resources))


if __name__ == '__main__':
    sys.exit(main())
