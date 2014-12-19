#!/usr/bin/env python3

import argparse
import os
import sys

from ros_buildfarm.catkin_workspace import call_catkin_make_isolated
from ros_buildfarm.catkin_workspace import clean_workspace
from ros_buildfarm.catkin_workspace import ensure_workspace_exists


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Invoke 'catkin_make_isolated' on a workspace while "
                    "enabling and running the tests")
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
        '--parent-result-space',
        help='The path of the parent result space')
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
        test_results_dir = os.path.join(args.workspace_root, 'test_results')
        arguments = [
            '--cmake-args', '-DCATKIN_ENABLE_TESTING=1',
            '-DCATKIN_SKIP_TESTING=0',
            '-DCATKIN_TEST_RESULTS_DIR=%s' % test_results_dir,
            '--catkin-make-args', '-j1']
        rc = call_catkin_make_isolated(
            args.rosdistro_name, args.workspace_root,
            arguments,
            parent_result_space=args.parent_result_space)
        if not rc:
            rc = call_catkin_make_isolated(
                args.rosdistro_name, args.workspace_root,
                arguments + ['tests'],
                parent_result_space=args.parent_result_space)
            if not rc:
                rc = call_catkin_make_isolated(
                    args.rosdistro_name, args.workspace_root,
                    arguments + ['run_tests'],
                    parent_result_space=args.parent_result_space)
    finally:
        if args.clean_after:
            clean_workspace(args.workspace_root)

    return rc


if __name__ == '__main__':
    sys.exit(main())
