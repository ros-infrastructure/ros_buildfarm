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
from ros_buildfarm.argument import add_argument_invalidate
from ros_buildfarm.argument import add_argument_pulp_base_url
from ros_buildfarm.argument import add_argument_pulp_distribution_name
from ros_buildfarm.argument import add_argument_pulp_password
from ros_buildfarm.argument import add_argument_pulp_task_timeout
from ros_buildfarm.argument import add_argument_pulp_username
from ros_buildfarm.common import Scope
from ros_buildfarm.pulp import PulpTaskPoller


def _get_recursive_dependencies(packages, target_names):
    to_remove = dict()
    new_names = set(target_names)

    while new_names:
        target_names = new_names
        new_names = set()

        for pkg in packages:
            if [r for r in pkg.requires if r[0] in target_names]:
                to_remove[pkg.pulp_href] = pkg
                new_names.add(pkg.name)
                new_names.update(prov[0] for prov in pkg.provides)

    return to_remove


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Import packages into a repository and publish it')
    parser.add_argument(
        'package_resources',
        nargs='*', metavar="PULP_HREF",
        help='Identifiers for packages which should be imported')
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

    pulp_config = pulp_rpm.Configuration(
        args.pulp_base_url, username=args.pulp_username,
        password=args.pulp_password)

    # https://pulp.plan.io/issues/5932
    pulp_config.safe_chars_for_path_param = '/'

    pulp_rpm_client = pulp_rpm.ApiClient(pulp_config)
    pulp_packages_api = pulp_rpm.ContentPackagesApi(pulp_rpm_client)
    pulp_distributions_api = pulp_rpm.DistributionsRpmApi(pulp_rpm_client)
    pulp_publications_api = pulp_rpm.PublicationsRpmApi(pulp_rpm_client)
    pulp_repos_api = pulp_rpm.RepositoriesRpmApi(pulp_rpm_client)

    pulp_task_poller = PulpTaskPoller(pulp_config, args.pulp_task_timeout)

    with Scope('SUBSECTION', 'inspecting repository state'):
        distribution = pulp_distributions_api.list(name=args.pulp_distribution_name).results[0]
        print('Pulp Distribution: %s%s' % (pulp_config.host, distribution.pulp_href))

        old_publication = pulp_publications_api.read(distribution.publication)
        print('Pulp Repository: %s%s' % (pulp_config.host, old_publication.repository))
        print('Pulp Publication (current): %s%s' % (pulp_config.host, old_publication.pulp_href))
        print('Pulp Repository Version (current): %s%s' % (
            pulp_config.host, old_publication.repository_version))

        packages_in_version_page = pulp_packages_api.list(
            repository_version=old_publication.repository_version, limit=200)
        packages_in_version = {pkg.pulp_href: pkg for pkg in packages_in_version_page.results}
        while packages_in_version_page.next:
            packages_in_version_page = pulp_packages_api.list(
                repository_version=old_publication.repository_version, limit=200,
                offset=len(packages_in_version))
            packages_in_version.update(
                {pkg.pulp_href: pkg for pkg in packages_in_version_page.results})

        assert packages_in_version_page.count == len(packages_in_version)
        print('Found %d packages in the repository' % len(packages_in_version))

        packages_to_add = {}
        packages_to_remove = {}

        # First, remove packages matching the explicit expression
        if args.invalidate_expression:
            compiled_expression = re.compile(args.invalidate_expression)
            for pkg in packages_in_version.values():
                if compiled_expression.match(pkg.name):
                    packages_to_remove[pkg.pulp_href] = pkg

        # Get the metadata for the packages we're adding
        for package_href in args.package_resources:
            package = packages_in_version.get(package_href) or pulp_packages_api.read(package_href)
            print('Importing package: %s-%s%s-%s.%s' % (
                package.name,
                (package.epoch + ':') if package.epoch != '0' else '',
                package.version,
                package.release,
                package.arch))

            if package.pulp_href in packages_in_version:
                packages_to_remove.pop(package.pulp_href, None)
                print('Package is already present - skipping: %s%s' % (
                    pulp_config.host, package.pulp_href))
                continue

            packages_to_add[package.pulp_href] = package

    with Scope('SUBSECTION', 'determining which packages to invalidate'):
        # Remove any packages with the same name
        package_names = set([pkg.name for pkg in packages_to_add.values()])
        for pkg in packages_in_version.values():
            if pkg.name in package_names:
                packages_to_remove[pkg.pulp_href] = pkg

        if args.invalidate:
            package_provides = package_names.union(
                prov[0] for pkg in packages_to_add.values() for prov in pkg.provides)
            packages_to_remove.update(
                _get_recursive_dependencies(packages_in_version.values(), package_provides))

    with Scope('SUBSECTION', 'committing changes'):
        print('Adding %d and removing %d from the repository' % (
            len(packages_to_add), len(packages_to_remove)))

        mod_data = pulp_rpm.RepositoryAddRemoveContent(
            add_content_units=list(packages_to_add.keys()),
            remove_content_units=list(packages_to_remove.keys()),
            base_version=old_publication.repository_version)

        print('Packages to add:\n- %s' % (
            '\n- '.join([pkg.location_href for pkg in packages_to_add.values()])
            if packages_to_add else '(none)'))
        print('Packages to remove:\n- %s' % (
            '\n- '.join([pkg.location_href for pkg in packages_to_remove.values()])
            if packages_to_remove else '(none)'))

        mod_task_href = pulp_repos_api.modify(old_publication.repository, mod_data).task
        mod_task = pulp_task_poller.wait_for_task(mod_task_href)

        try:
            print('Pulp Repository Version (new): %s%s' % (
                pulp_config.host, mod_task.created_resources[0]))
        except IndexError:
            print('The given additions result in no changes to the repository')
            return 0

    with Scope('SUBSECTION', 'publishing changes'):
        publish_data = pulp_rpm.RpmRpmPublication(
            repository_version=mod_task.created_resources[0])

        publish_task_href = pulp_publications_api.create(publish_data).task
        publish_task = pulp_task_poller.wait_for_task(publish_task_href)

        print('Pulp Publication (new): %s%s' % (
            pulp_config.host, publish_task.created_resources[0]))

    with Scope('SUBSECTION', 'updating distribution'):
        distribution.publication = publish_task.created_resources[0]

        distribute_task_href = pulp_distributions_api.partial_update(
            distribution.pulp_href, distribution).task
        pulp_task_poller.wait_for_task(distribute_task_href)

        print('Finished - changes are live at %s/' % distribution.base_url)


if __name__ == '__main__':
    sys.exit(main())
