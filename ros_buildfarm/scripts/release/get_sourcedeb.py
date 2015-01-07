#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_package_name
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_skip_download_sourcedeb
from ros_buildfarm.argument import add_argument_sourcedeb_dir
from ros_buildfarm.binarydeb_job import get_sourcedeb
from ros_buildfarm.common import Scope


def main(argv=sys.argv[1:]):
    with Scope('SUBSECTION', 'get sourcedeb'):
        parser = argparse.ArgumentParser(
            description='Get released package sourcedeb')
        add_argument_rosdistro_name(parser)
        add_argument_package_name(parser)
        add_argument_sourcedeb_dir(parser)
        add_argument_skip_download_sourcedeb(parser)
        args = parser.parse_args(argv)

        return get_sourcedeb(
            args.rosdistro_name, args.package_name, args.sourcedeb_dir,
            args.skip_download_sourcedeb)


if __name__ == '__main__':
    sys.exit(main())
