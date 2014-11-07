#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_package_name
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_sourcedeb_dir
from ros_buildfarm.sourcedeb_job import upload_sourcedeb


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Upload sourcedeb')
    add_argument_rosdistro_name(parser)
    add_argument_package_name(parser)
    add_argument_os_code_name(parser)
    add_argument_sourcedeb_dir(parser)
    parser.add_argument(
        '--upload-host',
        required=True,
        help='The host and base path to upload to')
    args = parser.parse_args(argv)

    return upload_sourcedeb(
        args.rosdistro_name, args.package_name, args.os_code_name,
        args.sourcedeb_dir, args.upload_host)


if __name__ == '__main__':
    sys.exit(main())
