#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.devel_job import add_arguments_for_target
from ros_buildfarm.devel_job import configure_devel_job


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'devel' job on Jenkins")
    add_arguments_for_target(parser)
    args = parser.parse_args(argv)

    return configure_devel_job(
        args.rosdistro_index_url, args.rosdistro_name, args.source_build_name,
        args.repository_name, args.os_name, args.os_code_name, args.arch)


if __name__ == '__main__':
    sys.exit(main())
