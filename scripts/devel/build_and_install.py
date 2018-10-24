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
import sys

from ros_buildfarm.catkin_workspace import call_catkin_make_isolated
from ros_buildfarm.catkin_workspace import clean_workspace
from ros_buildfarm.catkin_workspace import ensure_workspace_exists
from ros_buildfarm.common import Scope


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Invoke 'catkin_make_isolated --install' on a workspace")
    parser.add_argument(
        '--rosdistro-name',
        required=True,
        help='The name of the ROS distro to identify the setup file to be '
             'sourced (if available)')
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
            rc = call_catkin_make_isolated(
                args.rosdistro_name, args.workspace_root,
                ['--install', '--cmake-args', '-DCATKIN_SKIP_TESTING=1',
                 '--catkin-make-args', '-j1'],
                parent_result_spaces=parent_result_spaces)
    finally:
        if args.clean_after:
            clean_workspace(args.workspace_root)

    return rc


if __name__ == '__main__':
    sys.exit(main())
