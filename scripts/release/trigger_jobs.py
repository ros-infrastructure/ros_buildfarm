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
import sys

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_cache_dir
from ros_buildfarm.argument import add_argument_cause
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_groovy_script
from ros_buildfarm.argument import add_argument_missing_only
from ros_buildfarm.argument import add_argument_not_failed_only
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_source_only
from ros_buildfarm.trigger_job import trigger_release_jobs


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Trigger a set of jobs which artifacts are missing in ' +
                    'the repository')
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'release')
    add_argument_missing_only(parser)
    add_argument_source_only(parser)
    add_argument_not_failed_only(parser)
    add_argument_cause(parser)
    add_argument_groovy_script(parser)
    add_argument_cache_dir(parser, '/tmp/package_repo_cache')
    args = parser.parse_args(argv)

    return trigger_release_jobs(
        args.config_url, args.rosdistro_name, args.release_build_name,
        args.missing_only, args.source_only, args.cache_dir, cause=args.cause,
        groovy_script=args.groovy_script, not_failed_only=args.not_failed_only)


if __name__ == '__main__':
    sys.exit(main())
