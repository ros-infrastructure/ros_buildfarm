#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_repository_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.build_configuration import BuildConfiguration
from ros_buildfarm.build_configuration import BuildType
from ros_buildfarm.common import OSArchTarget
from ros_buildfarm.common import OSTarget
from ros_buildfarm.devel_job import configure_devel_job


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'devel' job on Jenkins")
    add_argument_rosdistro_index_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'source')
    add_argument_repository_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
    args = parser.parse_args(argv)

    return configure_devel_job(
        config=BuildConfiguration.from_args(args).resolve(BuildType.source),
        repo_name=args.repository_name,
        os_arch_target=OSArchTarget(OSTarget(args.os_name, args.os_code_name), args.arch)
    )


if __name__ == '__main__':
    sys.exit(main())
