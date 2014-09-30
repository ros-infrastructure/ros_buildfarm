#!/usr/bin/env python3

import argparse
import copy
import os
import sys

from ros_buildfarm import get_distribution_repository_keys
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Run the 'devel' job")
    parser.add_argument(
        '--rosdistro-index-url',
        required=True,
        help='The URL to the ROS distro index')
    parser.add_argument(
        '--rosdistro-name',
        help="The name of the ROS distro from the index")
    parser.add_argument(
        '--source-build-name',
        help="The name of the 'source-build' file from the index")
    parser.add_argument(
        '--repo-name',
        help="The name of the repository")
    parser.add_argument(
        '--os-name',
        help='The OS name')
    parser.add_argument(
        '--os-code-name',
        help='The OS code name')
    parser.add_argument(
        '--arch',
        help='The architecture')
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
    parser.add_argument(
        '--workspace-root',
        required=True,
        help='The root path of the workspace to compile')
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

    content = generate_dockerfile(data)
    dockerfile = os.path.join(args.dockerfile_dir, 'Dockerfile')
    print("Generating Dockerfile '%s':" % dockerfile)
    for line in content.splitlines():
        print(' ', line)
    with open(dockerfile, 'w') as h:
        h.write(content)


def generate_dockerfile(data):
    return expand_template('dockerfile/generate_docker_devel.em', data)


if __name__ == '__main__':
    main()
