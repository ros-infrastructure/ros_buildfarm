#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_append_timestamp
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.build_configuration import BuildConfiguration
from ros_buildfarm.release_job import configure_release_jobs


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'release' jobs on Jenkins")
    add_argument_rosdistro_index_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'release')
    add_argument_append_timestamp(parser)
    args = parser.parse_args(argv)

    return configure_release_jobs(BuildConfiguration.from_args(args))


if __name__ == '__main__':
    sys.exit(main())
