#!/usr/bin/env python3

import argparse
import os
import sys

from catkin_pkg.packages import find_packages
from ros_buildfarm.argument import \
    add_argument_distribution_repository_key_files
from ros_buildfarm.argument import add_argument_distribution_repository_urls
from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.common import get_binary_package_versions
from ros_buildfarm.common import get_debian_package_name
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.common import get_user_id


class DockerfileArgParser(object):
    """Argument parser class Dockerfile auto generation"""

    def __init__(self):
        # Create parser
        self.parser = argparse.ArgumentParser(
            description="Generate the 'Dockerfile's for the base docker images")  # Add arguments to parser
        self.parser.add_argument(
            '--rosdistro-name',
            required=True,
            help='The name of the ROS distro to identify the setup file to be '
                 'sourced')
        self.parser.add_argument(
            '--packages',
            nargs='+',
            help='What (meta)packages to include in the image.')
        self.parser.add_argument(
            '--template_packages',
            nargs='+',
            help='What packages to use for template.')
        self.parser.add_argument(
            '--os-name',
            required=True,
            help="The OS name (e.g. 'ubuntu')")
        self.parser.add_argument(
            '--os-code-name',
            required=True,
            help="The OS code name (e.g. 'trusty')")
        self.parser.add_argument(
            '--arch',
            required=True,
            help="The architecture (e.g. 'amd64')")
        # Add argument parsers to parser
        add_argument_distribution_repository_urls(self.parser)
        add_argument_distribution_repository_key_files(self.parser)
        add_argument_dockerfile_dir(self.parser)

    def parse(self, argv=sys.argv[1:]):
        """Parse a list of strings of arguments and return dict of data"""
        args = self.parser.parse_args(argv)

        # generate data for config
        data = {
            'os_name': args.os_name,
            'os_code_name': args.os_code_name,
            'arch': args.arch,

            'distribution_repository_urls': args.distribution_repository_urls,
            'distribution_repository_keys': get_distribution_repository_keys(
                args.distribution_repository_urls,
                args.distribution_repository_key_files),

            'packages': sorted(args.packages),
            'rosdistro': args.rosdistro_name,

            'template_packages': args.template_packages,
        }

        return data
