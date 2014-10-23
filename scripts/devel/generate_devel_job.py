#!/usr/bin/env python3

import argparse
import sys

from rosdistro import get_index_url

from ros_buildfarm.devel_job import configure_devel_job


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'devel' job on Jenkins")
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
    parser.add_argument(
        'repository_name',
        help="The name of the 'repository' from the distribution file")
    parser.add_argument(
        'os_name',
        help="The OS name from the 'source-build' file")
    parser.add_argument(
        'os_code_name',
        help="A OS code name from the 'source-build' file")
    parser.add_argument(
        'arch',
        help="An arch from the 'source-build' file")
    args = parser.parse_args(argv)

    return configure_devel_job(
        args.rosdistro_index_url, args.rosdistro_name, args.source_build_name,
        args.repository_name, args.os_name, args.os_code_name, args.arch)


if __name__ == '__main__':
    sys.exit(main())
