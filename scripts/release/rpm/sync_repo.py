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
import re
import sys

from ros_buildfarm.argument import add_argument_dry_run
from ros_buildfarm.argument import add_argument_invalidate
from ros_buildfarm.argument import add_argument_pulp_base_url
from ros_buildfarm.argument import add_argument_pulp_password
from ros_buildfarm.argument import add_argument_pulp_task_timeout
from ros_buildfarm.argument import add_argument_pulp_username
from ros_buildfarm.common import Scope
from ros_buildfarm.pulp import format_pkg_ver
from ros_buildfarm.pulp import PulpRpmClient


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Sync packages between pulp distributions')
    add_argument_dry_run(parser)
    add_argument_invalidate(parser)
    parser.add_argument(
        '--invalidate-expression',
        default=None,
        help='Any existing package names matching this expression will be removed')
    add_argument_pulp_base_url(parser)
    add_argument_pulp_password(parser)
    add_argument_pulp_task_timeout(parser)
    add_argument_pulp_username(parser)
    parser.add_argument(
        '--package-name-expression', default='.*',
        help='Expression to match against packages in the repositories')
    parser.add_argument(
        '--distribution-source-expression', required=True,
        help='Expression to match for source distribution names')
    parser.add_argument(
        '--distribution-dest-expression', required=True,
        help='Expression to transform matching source distribution names into destination names')
    args = parser.parse_args(argv)

    pulp_client = PulpRpmClient(
        args.pulp_base_url, args.pulp_username, args.pulp_password,
        task_timeout=args.pulp_task_timeout)

    dists_to_sync = []
    with Scope('SUBSECTION', 'enumerating distributions to sync'):
        dist_expression = re.compile(args.distribution_source_expression)
        distributions = {dist.name for dist in pulp_client.enumerate_distributions()}
        for dist_source in sorted(distributions):
            (dist_dest_pattern, matched_source) = dist_expression.subn(
                args.distribution_dest_expression, dist_source)
            if matched_source:
                dist_dest_matches = [
                    dist for dist in distributions if re.match(dist_dest_pattern, dist)]
                if not dist_dest_matches:
                    print(
                        "No distributions match destination pattern '%s'" % dist_dest_pattern,
                        file=sys.stderr)
                    return 1
                dists_to_sync.extend((dist_source, dist_dest) for dist_dest in dist_dest_matches)

        dists_to_sync = sorted(set(dists_to_sync))
        print('Syncing %d distributions:' % len(dists_to_sync))
        for dist_source_dest in dists_to_sync:
            print('- %s => %s' % dist_source_dest)

    packages = {}
    with Scope('SUBSECTION', 'enumerating packages to sync'):
        package_expression = re.compile(args.package_name_expression)
        for dist_source, _ in dists_to_sync:
            packages[dist_source] = {
                pkg.pulp_href: pkg
                for pkg in pulp_client.enumerate_pkgs_in_distribution_name(dist_source)
                if package_expression.match(pkg.name)}

        print('Matched %d packages from source distributions:' % (
            sum([len(pkgs) for pkgs in packages.values()])))
        for dist_source, _ in dists_to_sync:
            print('- %s: %d matching packages' % (dist_source, len(packages[dist_source])))

    with Scope('SUBSECTION', 'invalidation and committing changes'):
        for dist_source, dist_dest in dists_to_sync:
            packages_to_sync = packages[dist_source]
            if not packages_to_sync:
                print('Skipping sync from %s to %s' % (dist_source, dist_dest))
                continue
            print('Syncing %d packages from %s to %s...%s' % (
                len(packages_to_sync), dist_source, dist_dest,
                ' (dry run)' if args.dry_run else ''))
            new_pkgs, pkgs_removed = pulp_client.import_and_invalidate(
                dist_dest, packages_to_sync, args.invalidate_expression,
                args.invalidate, package_cache=packages_to_sync, dry_run=args.dry_run)
            print('- Added %d packages%s' % (
                len(new_pkgs), ' (dry run)' if args.dry_run else ''))
            for pkg in sorted(new_pkgs, key=lambda pkg: pkg.name):
                print('  - %s-%s' % (pkg.name, format_pkg_ver(pkg)))
            print('- Removed %d packages%s' % (
                len(pkgs_removed), ' (dry run)' if args.dry_run else ''))
            for pkg in sorted(pkgs_removed, key=lambda pkg: pkg.name):
                print('  - %s-%s' % (pkg.name, format_pkg_ver(pkg)))


if __name__ == '__main__':
    sys.exit(main())
