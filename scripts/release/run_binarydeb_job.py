#!/usr/bin/env python3

import argparse
import copy
import sys

from ros_buildfarm.argument import add_argument_append_timestamp
from ros_buildfarm.argument import add_argument_binarydeb_dir
from ros_buildfarm.argument import \
    add_argument_distribution_repository_key_files
from ros_buildfarm.argument import add_argument_distribution_repository_urls
from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_package_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_skip_download_sourcedeb
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.common import get_user_id
from ros_buildfarm.templates import create_dockerfile


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'binarydeb' job")
    add_argument_rosdistro_index_url(parser, required=True)
    add_argument_rosdistro_name(parser)
    add_argument_package_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
    add_argument_distribution_repository_urls(parser)
    add_argument_distribution_repository_key_files(parser)
    add_argument_binarydeb_dir(parser)
    add_argument_dockerfile_dir(parser)
    add_argument_skip_download_sourcedeb(parser)
    add_argument_append_timestamp(parser)
    args = parser.parse_args(argv)

    data = copy.deepcopy(args.__dict__)
    data.update({
        'uid': get_user_id(),

        'distribution_repository_urls': args.distribution_repository_urls,
        'distribution_repository_keys': get_distribution_repository_keys(
            args.distribution_repository_urls,
            args.distribution_repository_key_files),

        'skip_download_sourcedeb': args.skip_download_sourcedeb,

        'binarydeb_dir': '/tmp/binarydeb',
        'dockerfile_dir': '/tmp/docker_build_binarydeb',
    })
    create_dockerfile(
        'release/binarydeb_create_task.Dockerfile.em',
        data, args.dockerfile_dir)


if __name__ == '__main__':
    main()
