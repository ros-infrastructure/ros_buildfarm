#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.release_job import configure_release_jobs


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'release' jobs on Jenkins")
    add_argument_rosdistro_index_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'release')
    args = parser.parse_args(argv)

    return configure_release_jobs(
        args.rosdistro_index_url, args.rosdistro_name, args.release_build_name)


if __name__ == '__main__':
    sys.exit(main())
