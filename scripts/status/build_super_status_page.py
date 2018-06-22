#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_output_dir, add_argument_config_url
from ros_buildfarm.super_status import build_super_status_page


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'build_super_status_page' job")
    add_argument_config_url(parser)
    add_argument_output_dir(parser)
    parser.add_argument('distros', nargs='*', metavar='distro')
    args = parser.parse_args(argv)
    return build_super_status_page(args.config_url, output_dir=args.output_dir, distros=args.distros)


if __name__ == '__main__':
    main()
