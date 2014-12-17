#!/usr/bin/env python

from __future__ import print_function

import argparse
from em import BANGPATH_OPT
import sys

from catkin_pkg.packages import find_packages

from rosdistro import get_distribution_cache
from rosdistro import get_index
from rosdistro.manifest_provider import get_release_tag
from rosdistro.repository_specification import RepositorySpecification

from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.config import get_index as get_config_index
from ros_buildfarm.prerelease import add_overlay_arguments
from ros_buildfarm.prerelease import get_overlay_package_names
from ros_buildfarm.templates import expand_template


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

    args = parser.parse_args(argv)

    config = get_config_index(args.config_url)

    index = get_index(config.rosdistro_index_url)
    dist_cache = get_distribution_cache(index, args.rosdistro_name)
    dist_file = dist_cache.distribution_file

    # determine source repositories for overlay workspace
    packages = find_packages('catkin_workspace/src')
    underlay_package_names = [pkg.name for pkg in packages.values()]
    print("Underlay workspace contains %d packages:%s" %
          (len(underlay_package_names),
           ''.join(['\n- %s' % pkg_name
                    for pkg_name in sorted(underlay_package_names)])),
          file=sys.stderr)

    overlay_package_names = get_overlay_package_names(
        args.pkg, args.exclude_pkg, args.level,
        underlay_package_names, dist_cache.release_package_xmls, output=True)
    print("Overlay workspace will contain %d packages:%s" %
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
        (repositories[k], 'catkin_workspace_overlay/src/%s' % k)
        for k in sorted(repositories.keys())]

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
