#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_package_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.release_job import configure_release_job


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'release' job on Jenkins")
    add_argument_rosdistro_index_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'release')
    add_argument_package_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
    args = parser.parse_args(argv)

    return configure_release_job(
        args.rosdistro_index_url, args.rosdistro_name, args.release_build_name,
        args.repository_name, args.os_name, args.os_code_name)


if __name__ == '__main__':
    sys.exit(main())
