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

from pulpcore.client import pulp_rpm
from ros_buildfarm.argument import add_argument_pulp_base_url
from ros_buildfarm.argument import add_argument_pulp_distribution_name
from ros_buildfarm.argument import add_argument_pulp_password
from ros_buildfarm.argument import add_argument_pulp_resource_record
from ros_buildfarm.argument import add_argument_pulp_task_timeout
from ros_buildfarm.argument import add_argument_pulp_username
from ros_buildfarm.common import Scope


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

    pulp_config = pulp_rpm.Configuration(
        args.pulp_base_url, username=args.pulp_username,
        password=args.pulp_password)

    # https://pulp.plan.io/issues/5932
    pulp_config.safe_chars_for_path_param = '/'

    pulp_rpm_client = pulp_rpm.ApiClient(pulp_config)
    pulp_packages_api = pulp_rpm.ContentPackagesApi(pulp_rpm_client)
    pulp_distributions_api = pulp_rpm.DistributionsRpmApi(pulp_rpm_client)
    pulp_publications_api = pulp_rpm.PublicationsRpmApi(pulp_rpm_client)

    with Scope('SUBSECTION', 'list packages in the distribution'):
        distribution = pulp_distributions_api.list(
            name=args.pulp_distribution_name).results[0]
        print('Pulp Distribution: ' + pulp_config.host + distribution.pulp_href)

        publication = pulp_publications_api.read(distribution.publication)
        print('Pulp Publication: %s%s' % (pulp_config.host, publication.pulp_href))
        print('Pulp Repository: %s%s' % (pulp_config.host, publication.repository))
        print('Pulp Repository Version: %s%s' % (pulp_config.host, publication.repository_version))

        packages_in_version_page = pulp_packages_api.list(
            repository_version=publication.repository_version, limit=200)
        packages_in_version = list(packages_in_version_page.results)
        while packages_in_version_page.next:
            packages_in_version_page = pulp_packages_api.list(
                repository_version=publication.repository_version, limit=200,
                offset=len(packages_in_version))
            packages_in_version += packages_in_version_page.results

        print('Total packages in repository: %d' % len(packages_in_version))

        if args.package_name_expression:
            compiled_expression = re.compile(args.package_name_expression)
            packages_in_version = [
                pkg for pkg in packages_in_version if compiled_expression.match(pkg.name)]

        print('Found %d packages:' % len(packages_in_version))
        for pkg in packages_in_version:
            print('- %s-%s%s-%s' % (
                pkg.name,
                (pkg.epoch + ':') if pkg.epoch != '0' else '',
                pkg.version,
                pkg.release))

        if args.pulp_resource_record:
            print("Saving pulp resource record to '%s'." % args.pulp_resource_record)
            with open(args.pulp_resource_record, 'w') as resource_record:
                resource_record.write('PULP_RESOURCES=%s\n' % (
                    ' '.join([pkg.pulp_href for pkg in packages_in_version])))


if __name__ == '__main__':
    sys.exit(main())
