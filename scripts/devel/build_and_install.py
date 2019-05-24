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
import sys

from ros_buildfarm.argument import add_argument_build_tool
from ros_buildfarm.argument import add_argument_build_tool_args
from ros_buildfarm.common import Scope
from ros_buildfarm.workspace import call_build_tool
from ros_buildfarm.workspace import clean_workspace
from ros_buildfarm.workspace import ensure_workspace_exists


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
    args = parser.parse_args(argv)

    ensure_workspace_exists(args.workspace_root)

    if args.clean_before:
        clean_workspace(args.workspace_root)

    try:
        with Scope('SUBSECTION', 'build workspace in isolation and install'):
            parent_result_spaces = None
            if args.parent_result_space:
                parent_result_spaces = args.parent_result_space
            env = dict(os.environ)
            env['MAKEFLAGS'] = '-j1'
            rc = call_build_tool(
                args.build_tool, args.rosdistro_name, args.workspace_root,
                cmake_args=['-DBUILD_TESTING=0', '-DCATKIN_SKIP_TESTING=1'],
                args=args.build_tool_args,
                install=True,
                parent_result_spaces=parent_result_spaces, env=env)
    finally:
        if args.clean_after:
            clean_workspace(args.workspace_root)

    return rc


if __name__ == '__main__':
    sys.exit(main())
