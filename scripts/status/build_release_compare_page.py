#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_other_rosdistro_name
from ros_buildfarm.argument import add_argument_output_dir
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.status_page import build_release_compare_page


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Generate the release compare page')
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_other_rosdistro_name(parser)
    add_argument_output_dir(parser)
    parser.add_argument(
        '--copy-resources',
        action='store_true',
        help='Copy the resources instead of using symlinks')
    args = parser.parse_args(argv)

    return build_release_compare_page(
        args.config_url, [args.other_rosdistro_name, args.rosdistro_name],
        args.output_dir, copy_resources=args.copy_resources)


if __name__ == '__main__':
    main()
