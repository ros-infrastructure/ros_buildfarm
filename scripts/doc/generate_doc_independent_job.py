#!/usr/bin/env python3

import argparse
import sys

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.config import get_global_doc_build_files
from ros_buildfarm.config import get_index
from ros_buildfarm.config.doc_build_file import DOC_TYPE_MAKE
from ros_buildfarm.doc_job import configure_doc_independent_job


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'doc_independent' job on Jenkins")
    add_argument_config_url(parser)
    add_argument_build_name(parser, 'doc')
    args = parser.parse_args(argv)

    config = get_index(args.config_url)
    build_files = get_global_doc_build_files(config)
    build_file = build_files[args.doc_build_name]

    if build_file.documentation_type != DOC_TYPE_MAKE:
        print(("The doc build file '%s' has the wrong documentation type to " +
               "be used with this script") % args.doc_build_name,
              file=sys.stderr)
        return 1

    return configure_doc_independent_job(
        args.config_url, args.doc_build_name,
        config=config, build_file=build_file)


if __name__ == '__main__':
    sys.exit(main())
