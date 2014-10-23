#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.devel_job import add_arguments_for_source_build_file
from ros_buildfarm.devel_job import configure_devel_jobs


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'devel' jobs on Jenkins")
    add_arguments_for_source_build_file(parser)
    args = parser.parse_args(argv)

    return configure_devel_jobs(
        args.rosdistro_index_url, args.rosdistro_name, args.source_build_name)


if __name__ == '__main__':
    sys.exit(main())
