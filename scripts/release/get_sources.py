#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_package_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_source_dir
from ros_buildfarm.common import Scope
from ros_buildfarm.sourcedeb_job import get_sources


def main(argv=sys.argv[1:]):
    with Scope('SUBSECTION', 'get sources'):
        parser = argparse.ArgumentParser(
            description="Get released package sources")
        add_argument_rosdistro_index_url(parser)
        add_argument_rosdistro_name(parser)
        add_argument_package_name(parser)
        add_argument_os_name(parser)
        add_argument_os_code_name(parser)
        add_argument_source_dir(parser)
        args = parser.parse_args(argv)

        return get_sources(
            args.rosdistro_index_url, args.rosdistro_name, args.package_name,
            args.os_name, args.os_code_name, args.source_dir)


if __name__ == '__main__':
    sys.exit(main())
