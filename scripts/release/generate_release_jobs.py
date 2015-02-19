#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_groovy_script
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.release_job import configure_release_jobs


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'release' jobs on Jenkins")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'release')
    add_argument_groovy_script(parser)
    args = parser.parse_args(argv)

    return configure_release_jobs(
        args.config_url, args.rosdistro_name, args.release_build_name,
        groovy_script=args.groovy_script)


if __name__ == '__main__':
    sys.exit(main())
