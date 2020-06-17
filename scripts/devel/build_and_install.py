#!/usr/bin/env python3

# Copyright 2014, 2016 Open Source Robotics Foundation, Inc.
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
import subprocess
import sys

from ros_buildfarm.argument import add_argument_build_tool
from ros_buildfarm.argument import add_argument_build_tool_args
from ros_buildfarm.argument import add_argument_ros_version
from ros_buildfarm.argument import add_argument_run_abichecker
from ros_buildfarm.common import get_packages_in_workspaces
from ros_buildfarm.common import Scope
from ros_buildfarm.workspace import call_build_tool
from ros_buildfarm.workspace import clean_workspace
from ros_buildfarm.workspace import ensure_workspace_exists


def call_abi_checker(workspace_root, rosdistro_name, env):
    import rosdistro

    pkgs = get_packages_in_workspaces(workspace_root)
    pkg_names = [pkg.name for pkg in pkgs.values()]
    assert pkg_names, 'No packages found in the workspace'

    # Filter packages in source space that has been released
    index = rosdistro.get_index(rosdistro.get_index_url())
    dist_file = rosdistro.get_distribution_file(index, rosdistro_name)
    pkg_names_released = [
        pkg_name for pkg_name in pkg_names if pkg_name in dist_file.release_packages]

    assert len(workspace_root) == 1, 'auto-abi tool needs the implementation of multiple local-dir'
    # ROS_DISTRO is set in the env object
    cmd = ['auto-abi.py ' +
           '--orig-type ros-pkg --orig ' + ",".join(pkg_names_released) + ' ' +
           '--new-type ros-ws --new ' + os.path.join(workspace_root[0], 'install_isolated') + ' ' +
           '--report-dir ' + workspace_root[0] + ' ' +
           '--no-fail-if-empty ' +
           '--display-exec-time']
    print("Invoking '%s'" % (cmd))
    return subprocess.call(
        cmd, shell=True, stderr=subprocess.STDOUT, env=env)


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Invoke the build tool on a workspace')
    parser.add_argument(
        '--rosdistro-name',
        required=True,
        help='The name of the ROS distro to identify the setup file to be '
             'sourced (if available)')
    add_argument_build_tool(parser, required=True)
    add_argument_build_tool_args(parser)
    add_argument_run_abichecker(parser)
    parser.add_argument(
        '--workspace-root',
        required=True,
        help='The root path of the workspace to compile')
    parser.add_argument(
        '--parent-result-space', nargs='*',
        help='The paths of the parent result spaces')
    parser.add_argument(
        '--clean-before',
        action='store_true',
        help='The flag if the workspace should be cleaned before the '
             'invocation')
    parser.add_argument(
        '--clean-after',
        action='store_true',
        help='The flag if the workspace should be cleaned after the '
             'invocation')

    add_argument_ros_version(parser)

    args = parser.parse_args(argv)

    ensure_workspace_exists(args.workspace_root)

    if args.clean_before:
        clean_workspace(args.workspace_root)

    env = dict(os.environ)
    env.setdefault('MAKEFLAGS', '-j1')
    env.setdefault('ROS_DISTRO', args.rosdistro_name)

    try:
        with Scope('SUBSECTION', 'build workspace in isolation and install'):
            parent_result_spaces = None
            if args.parent_result_space:
                parent_result_spaces = args.parent_result_space
            cmake_args = ['-DBUILD_TESTING=0']
            if args.ros_version == 1:
                cmake_args.append('-DCATKIN_SKIP_TESTING=1')
            rc = call_build_tool(
                args.build_tool, args.rosdistro_name, args.workspace_root,
                cmake_args=cmake_args,
                args=args.build_tool_args,
                install=True,
                parent_result_spaces=parent_result_spaces, env=env)
    finally:
        if args.clean_after:
            clean_workspace(args.workspace_root)

    # only run abi-checker after successful builds and when requested
    if not rc and args.run_abichecker:
        with Scope('SUBSECTION', 'use abi checker'):
            abi_rc = call_abi_checker(
                [args.workspace_root],
                args.rosdistro_name,
                env)
        # Never fail a build because of abi errors but make them
        # unstable by printing MAKE_BUILD_UNSTABLE. Jenkins will
        # use a plugin to make it
        if abi_rc:
            print('MAKE_BUILD_UNSTABLE')

    return rc


if __name__ == '__main__':
    sys.exit(main())
