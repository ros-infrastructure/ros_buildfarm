#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_cache_dir
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_debian_repository_urls
from ros_buildfarm.argument import add_argument_output_dir
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.status_page import build_release_status_page


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'release_status_page' job")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'release')
    add_argument_debian_repository_urls(parser, nargs=3)
    add_argument_cache_dir(parser, '/tmp/debian_repo_cache')
    add_argument_output_dir(parser)
    args = parser.parse_args(argv)

    return build_release_status_page(
        args.config_url, args.rosdistro_name, args.release_build_name,
        args.debian_repository_urls[0], args.debian_repository_urls[1],
        args.debian_repository_urls[2], args.cache_dir, args.output_dir)


if __name__ == '__main__':
    main()
