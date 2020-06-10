#!/usr/bin/env python3

# Copyright 2014-2015 Open Source Robotics Foundation, Inc.
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
import copy
import sys

from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_build_tool
from ros_buildfarm.argument import add_argument_build_tool_args
from ros_buildfarm.argument import add_argument_build_tool_test_args
from ros_buildfarm.argument import add_argument_custom_rosdep_update_options
from ros_buildfarm.argument import add_argument_custom_rosdep_urls
from ros_buildfarm.argument import \
    add_argument_distribution_repository_key_files
from ros_buildfarm.argument import add_argument_distribution_repository_urls
from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.argument import add_argument_env_vars
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_repository_name
from ros_buildfarm.argument import add_argument_require_gpu_support
from ros_buildfarm.argument import add_argument_ros_version
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_run_abichecker
from ros_buildfarm.argument import extract_multiple_remainders
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.common import get_user_id
from ros_buildfarm.templates import create_dockerfile


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'devel' job")
    add_argument_rosdistro_index_url(parser, required=True)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'source')
    add_argument_repository_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
    add_argument_distribution_repository_urls(parser)
    add_argument_distribution_repository_key_files(parser)
    add_argument_custom_rosdep_urls(parser)
    parser.add_argument(
        '--prerelease-overlay',
        action='store_true',
        help='Operate on two catkin workspaces')
    add_argument_build_tool(parser, required=True)
    add_argument_custom_rosdep_update_options(parser)
    add_argument_ros_version(parser)
    add_argument_env_vars(parser)
    add_argument_dockerfile_dir(parser)
    add_argument_run_abichecker(parser)
    add_argument_require_gpu_support(parser)
    a1 = add_argument_build_tool_args(parser)
    a2 = add_argument_build_tool_test_args(parser)

    remainder_args = extract_multiple_remainders(argv, (a1, a2))
    args = parser.parse_args(argv)
    for k, v in remainder_args.items():
        setattr(args, k, v)

    data = copy.deepcopy(args.__dict__)
    data.update({
        'distribution_repository_urls': args.distribution_repository_urls,
        'distribution_repository_keys': get_distribution_repository_keys(
            args.distribution_repository_urls,
            args.distribution_repository_key_files),
        'custom_rosdep_urls': args.custom_rosdep_urls,
        'rosdep_update_options': args.custom_rosdep_update_options,
        'uid': get_user_id(),
    })
    create_dockerfile(
        'devel/devel_create_tasks.Dockerfile.em', data, args.dockerfile_dir)


if __name__ == '__main__':
    main()
