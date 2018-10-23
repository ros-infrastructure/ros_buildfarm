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
from ros_buildfarm.config import get_global_doc_build_files
from ros_buildfarm.config import get_index
from ros_buildfarm.config.doc_build_file import DOC_TYPE_DOCKER
from ros_buildfarm.config.doc_build_file import DOC_TYPE_MAKE
from ros_buildfarm.doc_job import configure_doc_independent_job


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'doc_independent' job on Jenkins")
    add_argument_config_url(parser)
    add_argument_build_name(parser, 'doc')
    add_argument_dry_run(parser)
    args = parser.parse_args(argv)

    config = get_index(args.config_url)
    build_files = get_global_doc_build_files(config)
    build_file = build_files[args.doc_build_name]

    if build_file.documentation_type not in (DOC_TYPE_MAKE, DOC_TYPE_DOCKER):
        print(("The doc build file '%s' has the wrong documentation type to " +
               "be used with this script") % args.doc_build_name,
              file=sys.stderr)
        return 1

    return configure_doc_independent_job(
        args.config_url, args.doc_build_name,
        config=config, build_file=build_file, dry_run=args.dry_run)


if __name__ == '__main__':
    sys.exit(main())
