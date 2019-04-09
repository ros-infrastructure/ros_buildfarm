#!/usr/bin/env python3

# Copyright 2015 Open Source Robotics Foundation, Inc.
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

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import \
    add_argument_distribution_repository_key_files
from ros_buildfarm.argument import add_argument_distribution_repository_urls
from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.argument import add_argument_install_apt_packages
from ros_buildfarm.argument import add_argument_install_pip_packages
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.common import get_user_id
from ros_buildfarm.templates import create_dockerfile


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'doc independent' job")
    add_argument_config_url(parser)
    add_argument_build_name(parser, 'doc')
    add_argument_install_apt_packages(parser)
    add_argument_install_pip_packages(parser)
    add_argument_distribution_repository_urls(parser)
    add_argument_distribution_repository_key_files(parser)
    add_argument_dockerfile_dir(parser)
    args = parser.parse_args(argv)

    data = copy.deepcopy(args.__dict__)
    data.update({
        'install_apt_packages': args.install_apt_packages,
        'install_pip_packages': args.install_pip_packages,
        'distribution_repository_urls': args.distribution_repository_urls,
        'distribution_repository_keys': get_distribution_repository_keys(
            args.distribution_repository_urls,
            args.distribution_repository_key_files),

        'uid': get_user_id(),
    })
    create_dockerfile(
        'doc/doc_independent_task.Dockerfile.em', data, args.dockerfile_dir)


if __name__ == '__main__':
    main()
