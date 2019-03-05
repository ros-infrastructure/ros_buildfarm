#!/usr/bin/env python3

# Copyright 2019 Open Source Robotics Foundation, Inc.
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
from pathlib import Path
import sys
from urllib.request import urlretrieve

from ros_buildfarm.argument import add_argument_above_depth
from ros_buildfarm.argument import add_argument_build_ignore
from ros_buildfarm.argument import add_argument_build_up_to
from ros_buildfarm.argument import add_argument_packages_select
from ros_buildfarm.argument import add_argument_repos_file_urls
from ros_buildfarm.argument import add_argument_test_branch
from ros_buildfarm.colcon import locate_packages
from ros_buildfarm.common import Scope
from ros_buildfarm.vcs import export_repositories, import_repositories
from ros_buildfarm.workspace import ensure_workspace_exists


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Create a workspace from vcs repos files.')
    add_argument_above_depth(parser)
    add_argument_build_ignore(parser)
    add_argument_build_up_to(parser)
    add_argument_packages_select(parser)
    add_argument_repos_file_urls(parser, required=True)
    add_argument_test_branch(parser)
    parser.add_argument(
        '--workspace-root',
        help='The path of the desired workspace',
        required=True)
    args = parser.parse_args(argv)

    ensure_workspace_exists(args.workspace_root)

    os.chdir(args.workspace_root)

    with Scope('SUBSECTION', 'fetch repos files(s)'):
        repos_files = []
        for repos_file_url in args.repos_file_urls:
            repos_file = os.path.join(args.workspace_root, os.path.basename(repos_file_url))
            print('Fetching \'%s\' to \'%s\'' % (repos_file_url, repos_file))
            urlretrieve(repos_file_url, repos_file)
            repos_files += [repos_file]

    with Scope('SUBSECTION', 'import repositories'):
        source_space = os.path.join(args.workspace_root, 'src')
        for repos_file in repos_files:
            print('Importing repositories from \'%s\'' % (repos_file))
            import_repositories(source_space, repos_file, args.test_branch)

    with Scope('SUBSECTION', 'vcs export --exact'):
        export_repositories(args.workspace_root)

    with Scope('SUBSECTION', 'mark package(s) to ignore'):
        if args.build_ignore:
            source_space = os.path.join(args.workspace_root, 'src')
            packages = locate_packages(source_space, args.build_ignore)
            for package_name, package_root in packages.items():
                print("Ignoring package '%s'" % (package_name,))
                Path(package_root, 'COLCON_IGNORE').touch()

    with Scope('SUBSECTION', 'select target package(s) in workspace'):
        packages = locate_packages(source_space)
        if args.packages_select:
            selected_packages = set()
            print('Selecting %d packages by name' % len(args.packages_select))
            if args.above_depth:
                packages_above_depth = [str(args.above_depth)] + \
                    args.packages_select
                after = locate_packages(
                    source_space,
                    packages_above_depth=packages_above_depth).keys()
                print('Selecting %d packages after current selection' %
                      (len(after) - len(args.packages_select)))
                selected_packages |= after
            if args.build_up_to:
                packages_up_to = selected_packages or args.packages_select
                up_to = locate_packages(
                    source_space,
                    packages_up_to=packages_up_to).keys()
                print('Selecting %d dependencies of current selection' %
                      (len(up_to) - len(packages_up_to)))
                selected_packages |= up_to
            if not selected_packages:
                selected_packages = locate_packages(
                    source_space,
                    packages_select=args.packages_select).keys()

            to_ignore = packages.keys() - selected_packages
            print('Ignoring %d packages to scope workspace' % len(to_ignore))
            for package in to_ignore:
                package_root = packages.pop(package)
                Path(package_root, 'COLCON_IGNORE').touch()

        print('There are %d packages which meet selection criteria' %
              len(packages))


if __name__ == '__main__':
    sys.exit(main())
