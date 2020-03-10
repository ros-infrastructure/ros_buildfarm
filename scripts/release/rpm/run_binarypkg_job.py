#!/usr/bin/env python3

# Copyright 2020 Open Source Robotics Foundation, Inc.
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

from ros_buildfarm.argument import add_argument_append_timestamp
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_binarypkg_dir
from ros_buildfarm.argument import \
    add_argument_distribution_repository_key_files
from ros_buildfarm.argument import add_argument_distribution_repository_urls
from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.argument import add_argument_env_vars
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_package_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_skip_download_sourcepkg
from ros_buildfarm.argument import add_argument_target_repository
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.common import get_user_id
from ros_buildfarm.templates import create_dockerfile
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'binarypkg' job")
    add_argument_rosdistro_index_url(parser, required=True)
    add_argument_rosdistro_name(parser)
    add_argument_package_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
    add_argument_distribution_repository_urls(parser)
    add_argument_distribution_repository_key_files(parser)
    add_argument_target_repository(parser)
    add_argument_dockerfile_dir(parser)
    add_argument_skip_download_sourcepkg(parser)
    add_argument_append_timestamp(parser)
    add_argument_env_vars(parser)
    add_argument_binarypkg_dir(parser)
    args = parser.parse_args(argv)

    data = copy.deepcopy(args.__dict__)
    data.update({
        'uid': get_user_id(),

        'distribution_repository_urls': args.distribution_repository_urls,
        'distribution_repository_keys': get_distribution_repository_keys(
            args.distribution_repository_urls,
            args.distribution_repository_key_files),
        'target_repository': os.path.join(args.target_repository, args.os_code_name, 'SRPMS'),

        'skip_download_sourcepkg': args.skip_download_sourcepkg,

        'sourcepkg_dir': os.path.join(args.binarypkg_dir, 'source'),
    })
    create_dockerfile(
        'release/rpm/binarypkg_task.Dockerfile.em',
        data, args.dockerfile_dir)

    with open(os.path.join(args.dockerfile_dir, 'mock_config.cfg'), 'w') as mock_cfg:
        mock_cfg.write(expand_template('release/rpm/mock_config.cfg.em', data))


if __name__ == '__main__':
    main()
