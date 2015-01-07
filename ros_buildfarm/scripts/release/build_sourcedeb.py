#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_source_dir
from ros_buildfarm.common import Scope
from ros_buildfarm.sourcedeb_job import build_sourcedeb


def main(argv=sys.argv[1:]):
    with Scope('SUBSECTION', 'build sourcedeb'):
        parser = argparse.ArgumentParser(
            description='Build package sourcedeb')
        add_argument_source_dir(parser)
        args = parser.parse_args(argv)

        return build_sourcedeb(args.source_dir)


if __name__ == '__main__':
    sys.exit(main())
