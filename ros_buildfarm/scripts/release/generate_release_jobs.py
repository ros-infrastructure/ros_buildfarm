# Copyright 2014-2016 Open Source Robotics Foundation, Inc.
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

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_dry_run
from ros_buildfarm.argument import add_argument_groovy_script
from ros_buildfarm.argument import add_argument_package_names
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.release_job import configure_release_jobs


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'release' jobs on Jenkins")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'release')
    add_argument_groovy_script(parser)
    add_argument_dry_run(parser)
    add_argument_package_names(parser)
    args = parser.parse_args(argv)

    return configure_release_jobs(
        args.config_url, args.rosdistro_name, args.release_build_name,
        groovy_script=args.groovy_script, dry_run=args.dry_run,
        whitelist_package_names=args.package_names)


if __name__ == '__main__':
    sys.exit(main())
