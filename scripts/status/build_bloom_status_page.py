#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_output_dir
from ros_buildfarm.bloom_status import build_bloom_status_page


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'build_bloom_status_page' job")
    add_argument_output_dir(parser)
    args = parser.parse_args(argv)

    return build_bloom_status_page(output_dir=args.output_dir)


if __name__ == '__main__':
    main()
