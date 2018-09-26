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
import subprocess
import sys

from ros_buildfarm.common import Scope
from ros_buildfarm.workspace import call_build_tool
from ros_buildfarm.workspace import clean_workspace
from ros_buildfarm.workspace import ensure_workspace_exists


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Invoke 'colcon build' on a workspace")
    parser.add_argument(
        '--workspace-root',
        required=True,
        help='The root path of the workspace to compile')
    parser.add_argument(
        '--rosdistro-name',
        required=True,
        help='The name of the ROS distro to identify the setup file to be '
             'sourced (if available)')
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
    parser.add_argument(
        '--testing',
        action='store_true',
        help='The flag if the workspace should be built with tests enabled '
             'and instead of installing the tests are ran')
    args = parser.parse_args(argv)

    ensure_workspace_exists(args.workspace_root)

    if args.clean_before:
        clean_workspace(args.workspace_root)

    try:
        with Scope('SUBSECTION', 'build workspace'):
            env = dict(os.environ)
            env['MAKEFLAGS'] = '-j1'

            parent_result_spaces = None
            if args.parent_result_space:
                parent_result_spaces = args.parent_result_space
            arguments = [
                '--cmake-args', '-DCMAKE_BUILD_TYPE=RelWithDebInfo',
                '-DBUILD_TESTING=0',
                '-DINSTALL_EXAMPLES=OFF', '-DSECURITY=ON',
                '--executor', 'sequential',
                '--event-handlers', 'console_direct+',
                '--merge-install', '--install-base', 'install_merged',
            ]
            if args.testing:
                arguments += [
                    '--cmake-args',
                    '-DBUILD_TESTING=1',
                    '--test-result-base', 'test_results',
                ]
            rc = call_build_tool(
                'colcon',
                args.rosdistro_name,
                args.workspace_root,
                arguments,
                parent_result_spaces=parent_result_spaces, env=env)

        if args.testing and not rc:
            with Scope('SUBSECTION', 'build tests'):
                arguments += ['--cmake-target', 'tests']
                rc = call_build_tool(
                    'colcon',
                    args.rosdistro_name,
                    args.workspace_root,
                    arguments + ['--cmake-target-skip-unavailable'],
                    parent_result_spaces=parent_result_spaces, env=env)

            if not rc:
                with Scope('SUBSECTION', 'run tests'):
                    arguments = [
                        '--executor', 'sequential',
                        '--event-handlers', 'console_direct+',
                        '--merge-install', '--install-base', 'install_merged',
                        '--test-result-base', 'test_results',
                        ]
                    rc = call_build_tool(
                        'colcon',
                        args.rosdistro_name,
                        args.workspace_root,
                        arguments,
                        parent_result_spaces=parent_result_spaces, env=env,
                        verb='test')

    finally:
        if args.clean_after:
            clean_workspace(args.workspace_root)

    return rc


if __name__ == '__main__':
    sys.exit(main())
