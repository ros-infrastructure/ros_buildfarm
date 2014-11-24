#!/usr/bin/env python3

import argparse
import copy
import os
import sys

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_cache_dir
from ros_buildfarm.argument import add_argument_missing_only
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_source_only
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.templates import create_dockerfile


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'trigger_jobs' job")
    add_argument_rosdistro_index_url(parser, required=True)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'release')
    parser.add_argument(
        '--distribution-repository-urls',
        nargs='*',
        default=[],
        help='The list of distribution repository URLs to use for installing '
             'dependencies')
    parser.add_argument(
        '--distribution-repository-key-files',
        nargs='*',
        default=[],
        help='The list of distribution repository key files to verify the '
             'corresponding URLs')
    add_argument_missing_only(parser)
    add_argument_source_only(parser)
    add_argument_cache_dir(parser)
    parser.add_argument(
        '--dockerfile-dir',
        default=os.curdir,
        help="The directory where the 'Dockerfile' will be generated")
    args = parser.parse_args(argv)

    data = copy.deepcopy(args.__dict__)
    data.update({
        'os_name': 'ubuntu',
        'os_code_name': 'trusty',

        'maintainer_email': 'dthomas+buildfarm@osrfoundation.org',
        'maintainer_name': 'Dirk Thomas',

        'distribution_repository_urls': args.distribution_repository_urls,
        'distribution_repository_keys': get_distribution_repository_keys(
            args.distribution_repository_urls,
            args.distribution_repository_key_files),

        'uid': os.getuid(),
    })
    create_dockerfile(
        'release/release_create_trigger_task.Dockerfile.em',
        data, args.dockerfile_dir)


if __name__ == '__main__':
    main()
