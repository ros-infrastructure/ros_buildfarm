#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.devel_job import configure_devel_jobs


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'devel' jobs on Jenkins")
    add_argument_rosdistro_index_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'source')
    args = parser.parse_args(argv)

    return configure_devel_jobs(
        args.rosdistro_index_url, args.rosdistro_name, args.source_build_name)


if __name__ == '__main__':
    sys.exit(main())
