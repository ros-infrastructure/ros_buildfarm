#!/usr/bin/env python3

# Copyright 2015-2016 Open Source Robotics Foundation, Inc.
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

from __future__ import print_function

import argparse
import sys

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_dry_run
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.config import get_doc_build_files
from ros_buildfarm.config import get_index
from ros_buildfarm.config.doc_build_file import DOC_TYPE_MANIFEST
from ros_buildfarm.doc_job import configure_doc_metadata_job


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'doc_metadata' job on Jenkins")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'doc')
    add_argument_dry_run(parser)
    args = parser.parse_args(argv)

    config = get_index(args.config_url)
    build_files = get_doc_build_files(config, args.rosdistro_name)
    build_file = build_files[args.doc_build_name]

    if build_file.documentation_type != DOC_TYPE_MANIFEST:
        print(("The doc build file '%s' has the wrong documentation type to " +
               "be used with this script") % args.doc_build_name,
              file=sys.stderr)
        return 1

    return configure_doc_metadata_job(
        args.config_url, args.rosdistro_name, args.doc_build_name,
        config=config, build_file=build_file, dry_run=args.dry_run)


if __name__ == '__main__':
    sys.exit(main())
