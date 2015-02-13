#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.config import get_doc_build_files
from ros_buildfarm.config import get_index
from ros_buildfarm.doc_job import configure_doc_metadata_job


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'doc_metadata' job on Jenkins")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'doc')
    args = parser.parse_args(argv)

    config = get_index(args.config_url)
    build_files = get_doc_build_files(config, args.rosdistro_name)
    build_file = build_files[args.doc_build_name]

    if not build_file.released_packages:
        print(("The doc build file '%s' must be used with the"
               "'generate_doc_maintenance_job' script") % args.doc_build_name,
              file=sys.stderr)
        return 1

    return configure_doc_metadata_job(
        args.config_url, args.rosdistro_name, args.doc_build_name,
        config=config, build_file=build_file)


if __name__ == '__main__':
    sys.exit(main())
