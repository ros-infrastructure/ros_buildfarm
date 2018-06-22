#!/usr/bin/env python3

import argparse
import copy
import sys

from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.common import get_user_id
from ros_buildfarm.templates import create_dockerfile


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'super_status_page' job")
    add_argument_dockerfile_dir(parser)
    add_argument_rosdistro_index_url(parser, required=True)
    args = parser.parse_args(argv)

    data = copy.deepcopy(args.__dict__)
    data.update({
        'uid': get_user_id(),
    })
    create_dockerfile(
        'status/super_status_page_task.Dockerfile.em',
        data, args.dockerfile_dir)


if __name__ == '__main__':
    main()
