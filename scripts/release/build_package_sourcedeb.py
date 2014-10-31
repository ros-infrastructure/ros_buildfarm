#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.sourcedeb_job import add_argument_source_dir
from ros_buildfarm.sourcedeb_job import build_package_sourcedeb


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Get released package sources")
    add_argument_source_dir(parser)
    args = parser.parse_args(argv)

    return build_package_sourcedeb(args.source_dir)


if __name__ == '__main__':
    sys.exit(main())
