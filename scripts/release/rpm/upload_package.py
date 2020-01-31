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
import os
import sys

from pulpcore.client import pulp_rpm
from ros_buildfarm.argument import add_argument_pulp_base_url
from ros_buildfarm.argument import add_argument_pulp_password
from ros_buildfarm.argument import add_argument_pulp_resource_record
from ros_buildfarm.argument import add_argument_pulp_task_timeout
from ros_buildfarm.argument import add_argument_pulp_username
from ros_buildfarm.common import Scope
from ros_buildfarm.pulp import PulpTaskPoller


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

    with Scope('SUBSECTION', 'upload package(s) to pulp'):
        pulp_config = pulp_rpm.Configuration(
            args.pulp_base_url, username=args.pulp_username,
            password=args.pulp_password)

        # https://pulp.plan.io/issues/5932
        pulp_config.safe_chars_for_path_param = '/'

        pulp_rpm_client = pulp_rpm.ApiClient(pulp_config)
        pulp_packages_api = pulp_rpm.ContentPackagesApi(pulp_rpm_client)

        pulp_task_poller = PulpTaskPoller(pulp_config, args.pulp_task_timeout)

        created_resources = []

        for file_path in args.package_file:
            relative_path = os.path.basename(file_path)

            print("Uploading '%s' to '%s'." % (file_path, pulp_config.host))
            upload_task_href = pulp_packages_api.create(
                relative_path, file=file_path).task
            upload_task = pulp_task_poller.wait_for_task(upload_task_href)

            created_rpm = pulp_packages_api.read(upload_task.created_resources[0])
            created_resources.append(created_rpm.pulp_href)

            print('Created RPM resource: %s%s' % (pulp_config.host, created_rpm.pulp_href))
            print("Package '%s' version: %s%s-%s" % (
                created_rpm.name,
                (created_rpm.epoch + ':') if created_rpm.epoch != '0' else '',
                created_rpm.version,
                created_rpm.release))

        if args.pulp_resource_record:
            print("Saving upload record to '%s'." % args.pulp_resource_record)
            with open(args.pulp_resource_record, 'w') as resource_record:
                resource_record.write('PULP_RESOURCES=%s\n' % ' '.join(created_resources))


if __name__ == '__main__':
    sys.exit(main())
