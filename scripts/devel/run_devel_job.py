#!/usr/bin/env python3

import argparse
import copy
import sys

from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import \
    add_argument_distribution_repository_key_files
from ros_buildfarm.argument import add_argument_distribution_repository_urls
from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_repository_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.common import get_user_id
from ros_buildfarm.templates import create_dockerfile


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'devel' job")
    add_argument_rosdistro_index_url(parser, required=True)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'source')
    add_argument_repository_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
    add_argument_distribution_repository_urls(parser)
    add_argument_distribution_repository_key_files(parser)
    parser.add_argument(
        '--prerelease-overlay',
        action='store_true',
        help='Operate on two catkin workspaces')
    add_argument_dockerfile_dir(parser)
    args = parser.parse_args(argv)

    data = copy.deepcopy(args.__dict__)
    data.update({
        'distribution_repository_urls': args.distribution_repository_urls,
        'distribution_repository_keys': get_distribution_repository_keys(
            args.distribution_repository_urls,
            args.distribution_repository_key_files),

        'uid': get_user_id(),
    })
    create_dockerfile(
        'devel/devel_create_tasks.Dockerfile.em', data, args.dockerfile_dir)


if __name__ == '__main__':
    main()
