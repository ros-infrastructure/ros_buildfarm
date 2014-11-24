#!/usr/bin/env python3

import argparse
import os
import sys

from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_binarydeb_dir
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.templates import create_dockerfile


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'Dockerfile' for installing the binarydeb")
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)  # TODO not yet supported
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
    add_argument_binarydeb_dir(parser)
    parser.add_argument(
        '--dockerfile-dir',
        default=os.curdir,
        help="The directory where the 'Dockerfile' will be generated")
    args = parser.parse_args(argv)

    # generate Dockerfile
    data = {
        'os_name': args.os_name,
        'os_code_name': args.os_code_name,

        'maintainer_email': 'dthomas+buildfarm@osrfoundation.org',
        'maintainer_name': 'Dirk Thomas',

        'distribution_repository_urls': args.distribution_repository_urls,
        'distribution_repository_keys': get_distribution_repository_keys(
            args.distribution_repository_urls,
            args.distribution_repository_key_files),
    }
    create_dockerfile(
        'release/binarydeb_install_task.Dockerfile.em',
        data, args.dockerfile_dir)

    # output hints about necessary volumes to mount
    print('Mount the following volumes when running the container:')
    print('  -v %s:/tmp/binarydeb:ro' % args.binarydeb_dir)


if __name__ == '__main__':
    main()
