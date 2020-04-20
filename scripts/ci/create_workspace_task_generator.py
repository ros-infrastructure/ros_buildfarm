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
import sys
from urllib.request import urlretrieve

from apt import Cache
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import \
    add_argument_distribution_repository_key_files
from ros_buildfarm.argument import add_argument_distribution_repository_urls
from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.argument import add_argument_env_vars
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_package_selection_args
from ros_buildfarm.argument import add_argument_repos_file_urls
from ros_buildfarm.argument import add_argument_repository_names
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_skip_rosdep_keys
from ros_buildfarm.argument import add_argument_test_branch
from ros_buildfarm.common import get_binary_package_versions
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.common import get_user_id
from ros_buildfarm.templates import create_dockerfile


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'Dockerfile' for the CI job")

    # Positional
    add_argument_rosdistro_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)

    add_argument_distribution_repository_key_files(parser)
    add_argument_distribution_repository_urls(parser)
    add_argument_dockerfile_dir(parser)
    add_argument_env_vars(parser)
    add_argument_package_selection_args(parser)
    add_argument_repos_file_urls(parser)
    add_argument_repository_names(parser, optional=True)
    add_argument_skip_rosdep_keys(parser)
    add_argument_test_branch(parser)
    parser.add_argument(
        '--workspace-root',
        nargs='+',
        help='The root path of the workspace to compile')
    args = parser.parse_args(argv)

    assert args.repos_file_urls or args.repository_names

    repos_file_names = []
    for index, repos_file_url in enumerate(args.repos_file_urls):
        repos_file_name = 'repositories-%d.repos' % (index)
        urlretrieve(repos_file_url, os.path.join(args.dockerfile_dir, repos_file_name))
        repos_file_names.append(repos_file_name)

    debian_pkg_names = [
        'git',
        'python3-apt',
        'python3-colcon-metadata',
        'python3-colcon-package-information',
        'python3-colcon-package-selection',
        'python3-colcon-recursive-crawl',
        'python3-colcon-ros',
        'python3-rosdep',
        'python3-vcstool',
    ]

    # get versions for build dependencies
    apt_cache = Cache()
    debian_pkg_versions = get_binary_package_versions(
        apt_cache, debian_pkg_names)

    # generate Dockerfile
    data = {
        'os_name': args.os_name,
        'os_code_name': args.os_code_name,
        'arch': args.arch,

        'distribution_repository_urls': args.distribution_repository_urls,
        'distribution_repository_keys': get_distribution_repository_keys(
            args.distribution_repository_urls,
            args.distribution_repository_key_files),

        'rosdistro_name': args.rosdistro_name,

        'custom_rosdep_urls': [],

        'uid': get_user_id(),

        'build_environment_variables': ['%s=%s' % key_value for key_value in args.env_vars.items()],

        'dependencies': debian_pkg_names,
        'dependency_versions': debian_pkg_versions,

        'repos_file_names': repos_file_names,
        'repository_names': args.repository_names,
        'test_branch': args.test_branch,

        'skip_rosdep_keys': args.skip_rosdep_keys,

        'package_selection_args': args.package_selection_args,

        'workspace_root': args.workspace_root,
    }
    create_dockerfile(
        'ci/create_workspace.Dockerfile.em', data, args.dockerfile_dir)


if __name__ == '__main__':
    main()
