#!/usr/bin/env python3

import argparse
import copy
import os
import sys

from ros_buildfarm.argument import add_argument_distribution_repository_key_files
from ros_buildfarm.argument import add_argument_distribution_repository_urls
from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_package_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.templates import create_dockerfile


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'sourcedeb' job")
    add_argument_rosdistro_index_url(parser, required=True)
    add_argument_rosdistro_name(parser)
    add_argument_package_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_distribution_repository_urls(parser)
    add_argument_distribution_repository_key_files(parser)
    parser.add_argument(
        '--source-dir',
        required=True,
        help='The directory where the package sources will be stored')
    add_argument_dockerfile_dir(parser)
    args = parser.parse_args(argv)

    data = copy.deepcopy(args.__dict__)
    data.update({
        'maintainer_email': 'dthomas+buildfarm@osrfoundation.org',
        'maintainer_name': 'Dirk Thomas',

        'distribution_repository_urls': args.distribution_repository_urls,
        'distribution_repository_keys': get_distribution_repository_keys(
            args.distribution_repository_urls,
            args.distribution_repository_key_files),

        'uid': os.getuid(),
    })
    create_dockerfile(
        'release/sourcedeb_task.Dockerfile.em', data, args.dockerfile_dir)


if __name__ == '__main__':
    main()
