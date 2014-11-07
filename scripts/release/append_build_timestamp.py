#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_package_name
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_sourcedeb_dir
from ros_buildfarm.binarydeb_job import append_build_timestamp
from ros_buildfarm.common import Scope


def main(argv=sys.argv[1:]):
    with Scope('SUBSECTION', 'append build timestamp'):
        parser = argparse.ArgumentParser(
            description='Append current timestamp to package version')
        add_argument_rosdistro_name(parser)
        add_argument_package_name(parser)
        add_argument_sourcedeb_dir(parser)
        args = parser.parse_args(argv)

        return append_build_timestamp(
            args.rosdistro_name, args.package_name, args.sourcedeb_dir)


if __name__ == '__main__':
    sys.exit(main())
