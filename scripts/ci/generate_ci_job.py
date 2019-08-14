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
import sys

from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_dry_run
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.ci_job import configure_ci_job


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'CI' job on Jenkins")

    # Positional
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'ci')
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)

    add_argument_dry_run(parser)
    args = parser.parse_args(argv)

    configure_ci_job(
        args.config_url, args.rosdistro_name, args.ci_build_name,
        args.os_name, args.os_code_name, args.arch, dry_run=args.dry_run)


if __name__ == '__main__':
    sys.exit(main())
