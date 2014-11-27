#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_cache_dir
from ros_buildfarm.argument import add_argument_debian_repository_urls
from ros_buildfarm.argument import add_argument_os_code_name_and_arch_tuples
from ros_buildfarm.argument import add_argument_output_dir
from ros_buildfarm.argument import add_argument_output_name
from ros_buildfarm.status_page import build_debian_repos_status_page


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'repos_status_page' job")
    add_argument_debian_repository_urls(parser)
    add_argument_os_code_name_and_arch_tuples(parser)
    add_argument_cache_dir(parser, '/tmp/debian_repo_cache')
    add_argument_output_name(parser)
    add_argument_output_dir(parser)
    args = parser.parse_args(argv)

    return build_debian_repos_status_page(
        args.debian_repository_urls, args.os_code_name_and_arch_tuples,
        args.cache_dir, args.output_name, args.output_dir)


if __name__ == '__main__':
    main()
