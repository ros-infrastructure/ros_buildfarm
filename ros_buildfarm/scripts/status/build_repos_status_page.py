# Copyright 2014 Open Source Robotics Foundation, Inc.
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

from ros_buildfarm.argument import add_argument_cache_dir
from ros_buildfarm.argument import add_argument_debian_repository_urls
from ros_buildfarm.argument import add_argument_os_code_name_and_arch_tuples
from ros_buildfarm.argument import add_argument_os_name_and_os_code_name_and_arch_tuples
from ros_buildfarm.argument import add_argument_output_dir
from ros_buildfarm.argument import add_argument_output_name
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.status_page import build_repos_status_page


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'repos_status_page' job")
    add_argument_rosdistro_name(parser)
    add_argument_debian_repository_urls(parser)
    add_argument_os_code_name_and_arch_tuples(parser, required=False)
    add_argument_os_name_and_os_code_name_and_arch_tuples(parser, required=False)
    add_argument_cache_dir(parser, '/tmp/package_repo_cache')
    add_argument_output_name(parser)
    add_argument_output_dir(parser)
    args = parser.parse_args(argv)

    # TODO: Remove when --os-code-name-and-arch-tuples is removed
    if not args.os_name_and_os_code_name_and_arch_tuples:
        parser.error(
            'the following arguments are required: --os-name-and-os-code-name-and-arch-tuples')

    return build_repos_status_page(
        args.rosdistro_name, args.debian_repository_urls,
        args.os_name_and_os_code_name_and_arch_tuples, args.cache_dir, args.output_name,
        args.output_dir)


if __name__ == '__main__':
    sys.exit(main())
