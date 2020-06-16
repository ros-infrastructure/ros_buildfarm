#!/usr/bin/env python3

# Copyright 2020 Open Source Robotics Foundation, Inc.
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


import argparse
import copy
import sys

from ros_buildfarm.argument import add_argument_cache_dir
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_return_zero
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.config import get_index as get_config_index
from ros_buildfarm.config import get_release_build_files
from ros_buildfarm.release_job import partition_packages
from ros_buildfarm.status_page import get_jenkins_job_urls
from rosdistro import get_distribution_cache
from rosdistro import get_distribution_file
from rosdistro import get_index


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Audit the rosdistro for packages failing to build.')
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_cache_dir(parser, '/tmp/package_repo_cache')
    add_argument_return_zero(parser)
    args = parser.parse_args(argv)

    recommended_action_count = run_audit(args.config_url, args.rosdistro_name, args.cache_dir)
    return 1 if recommended_action_count and not args.return_zero else 0


def run_audit(config_url, rosdistro_name, cache_dir):
    config = get_config_index(config_url)
    index = get_index(config.rosdistro_index_url)
    dist_file = get_distribution_file(index, rosdistro_name)
    dist_cache = get_distribution_cache(index, rosdistro_name)
    build_files = get_release_build_files(config, rosdistro_name)
    missing_packages = {}
    for bf_name, bf_value in build_files.items():
        missing_packages[bf_name] = copy.deepcopy(bf_value.targets)
        for target in bf_value.get_targets_list():
            all_pkgs, missing_pkgs = partition_packages(
                config_url, rosdistro_name, bf_name, target, cache_dir,
                deduplicate_dependencies=True, dist_cache=dist_cache)
            missing_packages[bf_name][target] = missing_pkgs
            if 'all' in missing_packages[bf_name]:
                missing_packages[bf_name]['all'] &= missing_pkgs
            else:
                missing_packages[bf_name]['all'] = missing_pkgs

            if 'all' in missing_packages:
                missing_packages['all'] &= missing_pkgs
            else:
                missing_packages['all'] = missing_pkgs

    recommended_actions = len(missing_packages['all'])
    print('# Sync preparation report for %s' % rosdistro_name)
    print('Prepared for configuration: %s' % config_url)
    print('Prepared for rosdistro index: %s' % config.rosdistro_index_url)
    print('\n\n')

    if missing_packages['all']:
        print('## Packages failing on all platforms\n\n'
              'These releases are recommended to be rolled back:\n')
        for mp in sorted(missing_packages['all']):
            print(' - %s ' % mp)
        print('\n\n')
    else:
        print('## No packages detected failing on all platforms\n\n')

    def get_package_repository_link(dist_file, pkg_name):
        """Return the best guess of the url for filing a ticket against the package."""
        pkg = dist_file.release_packages[pkg_name]
        repo_name = pkg.repository_name
        repo = dist_file.repositories[repo_name]
        if repo.source_repository and repo.source_repository.url:
            return repo.source_repository.url
        if repo.release_repository and repo.release_repository.url:
            return repo.release_repository.url
        return None

    for bf_name in build_files.keys():
        print('## Audit of buildfile %s\n\n' % bf_name)
        # TODO(tfoote) use rosdistro API to print the release build config for editing
        recommended_blacklists = sorted(missing_packages[bf_name]['all'] - missing_packages['all'])
        recommended_actions += len(recommended_blacklists)
        if not recommended_blacklists:
            print('Congratulations! '
                  'No packages are failing to build on all targets for this buildfile.\n\n')
            continue
        print('Attention! '
              'The following packages are failing to build on all targets for this buildfile. '
              'It is recommended to blacklist them in the buildfile.\n\n')
        for rb in recommended_blacklists:
            print(' - %s:' % rb)
            jenkins_urls = get_jenkins_job_urls(
                rosdistro_name,
                config.jenkins_url,
                bf_name,
                build_files[bf_name].get_targets_list())
            url = get_package_repository_link(dist_file, rb)
            print('   - Suggested ticket location [%s](%s)' % (url, url))
            print('')
            print('   Title:')
            print('')
            print('       %s in %s fails to build on %s targets' % (rb, rosdistro_name, bf_name))
            print('')
            print('   Body:')
            print('')
            print('       The package %s in %s has been detected as not building'
                  % (rb, rosdistro_name) +
                  ' on all platforms in the buildfile %s.' % (bf_name) +
                  ' The release manager for %s will consider disabling' % (rosdistro_name) +
                  ' this build if it continues to fail to build.')
            print('       - jenkins_urls:')
            for target, ju in jenkins_urls.items():
                target_str = ' '.join([x for x in target])
                url = ju.format(pkg=rb)
                print('          - [%s](%s)' % (target_str, url))
                # TODO(tfoote) embed build status when buildfarm has https
                # print('    - %s [![Build Status](%s)](%s)' % (' '.join([x for x in target]),
                #       ju.format(pkg = rb) + '/badge/icon', ju.format(pkg = rb)))
            print('       This is being filed because this package is about to be blacklisted.'
                  ' If this ticket is resolved please review whether it can be removed from'
                  ' the blacklist that should cross reference here.')
            print('')

    return recommended_actions


if __name__ == '__main__':
    sys.exit(main())
