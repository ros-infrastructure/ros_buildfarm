#!/usr/bin/env python3

import argparse
import sys

from rosdistro import get_index_url

from ros_buildfarm.devel_job import configure_devel_jobs


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'devel' jobs on Jenkins")
    parser.add_argument(
        '--rosdistro-index-url',
        default=get_index_url(),
        help=("The URL to the ROS distro index (default: '%s', based on the " +
              "environment variable ROSDISTRO_INDEX_URL") % get_index_url())
    parser.add_argument(
        'rosdistro_name',
        help="The name of the ROS distro from the index")
    parser.add_argument(
        'source_build_name',
        help="The name of the 'source-build' file from the index")
    args = parser.parse_args(argv)

    return configure_devel_jobs(
        args.rosdistro_index_url, args.rosdistro_name, args.source_build_name)


if __name__ == '__main__':
    sys.exit(main())
