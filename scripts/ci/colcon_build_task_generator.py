#!/usr/bin/env python3

# Copyright 2018 Open Source Robotics Foundation, Inc.
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

from apt import Cache

from ros_buildfarm.argument import \
    add_argument_distribution_repository_key_files
from ros_buildfarm.argument import add_argument_distribution_repository_urls
from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.common import get_binary_package_versions
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.common import get_user_id
from ros_buildfarm.templates import create_dockerfile


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'Dockerfile' for the CI job")
    parser.add_argument(
        '--workspace-root',
        nargs='+',
        help='The root path of the workspace to compile')
    parser.add_argument(
        '--rosdistro-name',
        required=True,
        help='The name of the ROS distro to identify the setup file to be '
             'sourced (if available)')
    parser.add_argument(
        '--os-name',
        required=True,
        help="The OS name (e.g. 'ubuntu')")
    parser.add_argument(
        '--os-code-name',
        required=True,
        help="The OS code name (e.g. 'xenial')")
    parser.add_argument(
        '--arch',
        required=True,
        help="The architecture (e.g. 'amd64')")
    add_argument_distribution_repository_urls(parser)
    add_argument_distribution_repository_key_files(parser)
    add_argument_dockerfile_dir(parser)
    args = parser.parse_args(argv)

    debian_pkg_names = [
        'build-essential',
        'python3-colcon-core',
        'python3-colcon-defaults',
        'python3-colcon-library-path',
        'python3-colcon-metadata',
        'python3-colcon-output',
        'python3-colcon-package-information',
        'python3-colcon-package-selection',
        'python3-colcon-parallel-executor',
        'python3-colcon-powershell',
        'python3-colcon-python-setup-py',
        'python3-colcon-recursive-crawl',
        'python3-colcon-test-result',
        'python3-colcon-cmake',
        'python3-colcon-ros',
    ]
    print('Always install the following generic dependencies:')
    for debian_pkg_name in sorted(debian_pkg_names):
        print('  -', debian_pkg_name)

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

        'uid': get_user_id(),
        'rosdistro_name': args.rosdistro_name,

        'dependencies': debian_pkg_names,
        'dependency_versions': debian_pkg_versions,

        'parent_result_space': [],
    }
    create_dockerfile(
        'ci/colcon_build.Dockerfile.em', data, args.dockerfile_dir)

    # output hints about necessary volumes to mount
    ros_buildfarm_basepath = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..'))
    print('Mount the following volumes when running the container:')
    print('  -v %s:/tmp/ros_buildfarm:ro' % ros_buildfarm_basepath)
    print('  -v %s:/tmp/workspace' % args.workspace_root[-1])


if __name__ == '__main__':
    main()
