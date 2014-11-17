#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_cache_dir
from ros_buildfarm.argument import add_argument_debian_repository_urls
from ros_buildfarm.argument import add_argument_output_dir
from ros_buildfarm.status_page import build_debian_repos_status_page


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'repos_status_page' job")
    add_argument_debian_repository_urls(parser)
    parser.add_argument(
        '--os-code-name-and-arch-tuples',
        nargs='+',
        required=True,
        help="The colon separated tuple containing an OS code name and an " +
             "architecture (e.g. 'trusty:amd64')")
    add_argument_cache_dir(parser, '/tmp/status_page_cache')
    parser.add_argument(
        '--output-name',
        required=True,
        help='The name of the generated html file (without the extensions)')
    add_argument_output_dir(parser)
    args = parser.parse_args(argv)

    return build_debian_repos_status_page(
        args.debian_repository_urls, args.os_code_name_and_arch_tuples,
        args.cache_dir, args.output_name, args.output_dir)


if __name__ == '__main__':
    main()
