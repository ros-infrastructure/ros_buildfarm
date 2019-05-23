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

from apt import Cache
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_tool
from ros_buildfarm.argument import add_argument_build_tool_args
from ros_buildfarm.argument import \
    add_argument_distribution_repository_key_files
from ros_buildfarm.argument import add_argument_distribution_repository_urls
from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.argument import add_argument_env_vars
from ros_buildfarm.argument import add_argument_install_packages
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_ros_version
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_testing
from ros_buildfarm.argument import check_len_action
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

    add_argument_build_tool(parser, required=True)
    add_argument_build_tool_args(parser)
    add_argument_distribution_repository_key_files(parser)
    add_argument_distribution_repository_urls(parser)
    add_argument_dockerfile_dir(parser)
    add_argument_env_vars(parser)
    add_argument_install_packages(parser)
    add_argument_ros_version(parser)
    add_argument_testing(parser)
    parser.add_argument(
        '--workspace-root', nargs='*',
        action=check_len_action(1, 2),
        help='The root path of the workspace to compile')
    args = parser.parse_args(argv)

    apt_cache = Cache()

    debian_pkg_names = set(['build-essential'])
    debian_pkg_names.update(args.install_packages)
    if args.build_tool == 'colcon':
        debian_pkg_names.update([
            'python3-catkin-pkg-modules',
            'python3-colcon-output',
            'python3-colcon-parallel-executor',
            'python3-colcon-ros',
            'python3-colcon-test-result',
            'python3-rosdistro-modules',
        ])

    print('Always install the following generic dependencies:')
    for debian_pkg_name in sorted(debian_pkg_names):
        print('  -', debian_pkg_name)

    install_list = 'install_list.txt'
    write_install_list(
        os.path.join(args.dockerfile_dir, install_list),
        debian_pkg_names, apt_cache)
    install_lists = [install_list, 'install_list_build.txt']
    if args.testing:
        install_lists.append('install_list_test.txt')

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

        'uid': get_user_id(),

        'build_tool': args.build_tool,
        'build_tool_args': args.build_tool_args,
        'ros_version': args.ros_version,

        'build_environment_variables': args.env_vars,

        'install_lists': install_lists,
        'dependencies': [],
        'dependency_versions': [],

        'testing': args.testing,
        'prerelease_overlay': len(args.workspace_root) > 1,
    }
    create_dockerfile(
        'devel/devel_task.Dockerfile.em', data, args.dockerfile_dir)

    # output hints about necessary volumes to mount
    ros_buildfarm_basepath = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..'))
    print('Mount the following volumes when running the container:')
    print('  -v %s:/tmp/ros_buildfarm:ro' % ros_buildfarm_basepath)
    if len(args.workspace_root) == 1:
        print('  -v %s:/tmp/ws' % args.workspace_root[0])
    else:
        for i, workspace_root in enumerate(args.workspace_root[0:-1]):
            print('  -v %s:/tmp/ws%s' % (workspace_root, i or ''))
        print('  -v %s:/tmp/ws_overlay' % args.workspace_root[-1])


def write_install_list(install_list_path, debian_pkg_names, apt_cache):
    debian_pkg_versions = get_binary_package_versions(apt_cache, debian_pkg_names)
    with open(install_list_path, 'w') as out_file:
        for pkg, pkg_version in sorted(debian_pkg_versions.items()):
            out_file.write('%s=%s\n' % (pkg, pkg_version))


if __name__ == '__main__':
    main()
