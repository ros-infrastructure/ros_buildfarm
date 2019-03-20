#!/usr/bin/env python

# Copyright 2014-2015 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import argparse
import json
import sys

from catkin_pkg.packages import find_packages
from em import BANGPATH_OPT
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.config import get_index as get_config_index
from ros_buildfarm.prerelease import add_overlay_arguments
from ros_buildfarm.prerelease import get_overlay_package_names
from ros_buildfarm.templates import expand_template
from rosdistro import get_distribution_cache
from rosdistro import get_index
from rosdistro.manifest_provider import get_release_tag
from rosdistro.repository_specification import RepositorySpecification


def main(argv=sys.argv[1:]):
    global templates
    parser = argparse.ArgumentParser(
        description="Generate a 'prerelease overlay' script")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
    add_overlay_arguments(parser)
    parser.add_argument(
        '--underlay-packages', nargs='+',
        help='Names of packages on which the overlay builds '
             '(by default package names come from packages found in '
             "'ws/src')"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--json', action='store_true',
        help='Output overlay information as JSON instead of a shell script'
    )
    group.add_argument(
        '--vcstool', action='store_true',
        help='Output overlay information as vcstool repos file'
    )

    args = parser.parse_args(argv)

    config = get_config_index(args.config_url)

    index = get_index(config.rosdistro_index_url)
    dist_cache = get_distribution_cache(index, args.rosdistro_name)
    dist_file = dist_cache.distribution_file

    # determine source repositories for overlay workspace
    underlay_package_names = args.underlay_packages
    if underlay_package_names is None:
        packages = find_packages('ws/src')
        underlay_package_names = [pkg.name for pkg in packages.values()]
    print('Underlay workspace contains %d packages:%s' %
          (len(underlay_package_names),
           ''.join(['\n- %s' % pkg_name
                    for pkg_name in sorted(underlay_package_names)])),
          file=sys.stderr)

    overlay_package_names = get_overlay_package_names(
        args.pkg, args.exclude_pkg, args.level,
        underlay_package_names, dist_cache.release_package_xmls, output=True)
    print('Overlay workspace will contain %d packages:%s' %
          (len(overlay_package_names),
           ''.join(['\n- %s' % pkg_name
                    for pkg_name in sorted(overlay_package_names)])),
          file=sys.stderr)

    repositories = {}
    for pkg_name in overlay_package_names:
        repositories[pkg_name] = \
            get_repository_specification_for_released_package(
                dist_file, pkg_name)
    scms = [
        (repositories[k], 'ws_overlay/src/%s' % k)
        for k in sorted(repositories.keys())]

    if args.json:
        print(json.dumps([vars(r) for r, p in scms], sort_keys=True, indent=2))
    elif args.vcstool:
        print('repositories:')
        for r, p in scms:
            print('  %s:' % p)
            print('    type: ' + r.type)
            print('    url: ' + r.url)
            print('    version: ' + r.version)
    else:
        value = expand_template(
            'prerelease/prerelease_overlay_script.sh.em', {
                'scms': scms},
            options={BANGPATH_OPT: False})
        print(value)


def get_repository_specification_for_released_package(dist_file, pkg_name):
    repo_name = dist_file.release_packages[pkg_name].repository_name
    release_repo = dist_file.repositories[repo_name].release_repository
    version_tag = get_release_tag(release_repo, pkg_name)
    return RepositorySpecification(
        pkg_name, {
            'type': 'git',
            'url': release_repo.url,
            'version': version_tag,
        })


if __name__ == '__main__':
    sys.exit(main())
