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
import copy
import os
import sys
from urllib.request import urlretrieve

from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_tool
from ros_buildfarm.argument import add_argument_build_tool_args
from ros_buildfarm.argument import add_argument_build_tool_test_args
from ros_buildfarm.argument import \
    add_argument_distribution_repository_key_files
from ros_buildfarm.argument import add_argument_distribution_repository_urls
from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.argument import add_argument_env_vars
from ros_buildfarm.argument import add_argument_install_packages
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_package_selection_args
from ros_buildfarm.argument import add_argument_repos_file_urls
from ros_buildfarm.argument import add_argument_repository_names
from ros_buildfarm.argument import add_argument_ros_version
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_skip_rosdep_keys
from ros_buildfarm.argument import add_argument_test_branch
from ros_buildfarm.argument import extract_multiple_remainders
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.common import get_user_id
from ros_buildfarm.templates import create_dockerfile


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'CI' job")

    # Positional
    add_argument_rosdistro_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)

    add_argument_build_tool(parser, required=True)
    add_argument_distribution_repository_key_files(parser)
    add_argument_distribution_repository_urls(parser)
    add_argument_dockerfile_dir(parser)
    add_argument_env_vars(parser)
    add_argument_install_packages(parser)
    a1 = add_argument_package_selection_args(parser)
    a2 = add_argument_build_tool_args(parser)
    a3 = add_argument_build_tool_test_args(parser)
    add_argument_repos_file_urls(parser)
    add_argument_repository_names(parser, optional=True)
    add_argument_ros_version(parser)
    add_argument_skip_rosdep_keys(parser)
    add_argument_test_branch(parser)
    parser.add_argument(
        '--workspace-mount-point', nargs='*',
        help='Locations within the docker image where the workspace(s) '
             'will be mounted when the docker image is run.')

    remainder_args = extract_multiple_remainders(argv, (a1, a2, a3))
    args = parser.parse_args(argv)
    for k, v in remainder_args.items():
        setattr(args, k, v)

    assert args.repos_file_urls or args.repository_names

    repos_file_names = []
    for index, repos_file_url in enumerate(args.repos_file_urls):
        repos_file_name = 'repositories-%d.repos' % (index)
        urlretrieve(repos_file_url, os.path.join(args.dockerfile_dir, repos_file_name))
        repos_file_names.append(repos_file_name)

    data = copy.deepcopy(args.__dict__)
    data.update({
        'distribution_repository_urls': args.distribution_repository_urls,
        'distribution_repository_keys': get_distribution_repository_keys(
            args.distribution_repository_urls,
            args.distribution_repository_key_files),
        'repos_file_names': repos_file_names,
        'uid': get_user_id(),
    })
    create_dockerfile(
        'ci/ci_create_tasks.Dockerfile.em', data, args.dockerfile_dir)


if __name__ == '__main__':
    main()
