#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_cache_dir
from ros_buildfarm.argument import add_argument_cause
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_groovy_script
from ros_buildfarm.argument import add_argument_missing_only
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_source_only
from ros_buildfarm.trigger_job import trigger_release_jobs


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Trigger a set of jobs which artifacts are missing in ' +
                    'the repository')
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'release')
    add_argument_missing_only(parser)
    add_argument_source_only(parser)
    add_argument_cause(parser)
    add_argument_groovy_script(parser)
    add_argument_cache_dir(parser, '/tmp/debian_repo_cache')
    args = parser.parse_args(argv)

    return trigger_release_jobs(
        args.config_url, args.rosdistro_name, args.release_build_name,
        args.missing_only, args.source_only, args.cache_dir, cause=args.cause,
        groovy_script=args.groovy_script)


if __name__ == '__main__':
    sys.exit(main())
