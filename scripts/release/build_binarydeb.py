#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_source_dir
from ros_buildfarm.binarydeb_job import build_binarydeb


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Build package binarydeb')
    add_argument_source_dir(parser)
    args = parser.parse_args(argv)

    return build_binarydeb(args.source_dir)


if __name__ == '__main__':
    sys.exit(main())
