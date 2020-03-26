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
from ros_buildfarm.argument import add_argument_pulp_base_url
from ros_buildfarm.argument import add_argument_pulp_password
from ros_buildfarm.argument import add_argument_pulp_task_timeout
from ros_buildfarm.argument import add_argument_pulp_username
from ros_buildfarm.common import Scope
from ros_buildfarm.pulp import PulpRpmClient


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Mirror a remote RPM repository to a pulp distribution')
    add_argument_dry_run(parser)
    add_argument_pulp_base_url(parser)
    add_argument_pulp_password(parser)
    add_argument_pulp_task_timeout(parser)
    add_argument_pulp_username(parser)
    parser.add_argument(
        '--remote-source-expression', required=True,
        help='Expression to match for pulp remote names')
    parser.add_argument(
        '--distribution-dest-expression', required=True,
        help='Expression to transform matching source remote names '
             'into destination distribution names')
    args = parser.parse_args(argv)

    pulp_client = PulpRpmClient(
        args.pulp_base_url, args.pulp_username, args.pulp_password,
        task_timeout=args.pulp_task_timeout)

    dists_to_sync = []
    with Scope('SUBSECTION', 'enumerating remotes and distributions to sync'):
        remote_expression = re.compile(args.remote_source_expression)
        distributions = {dist.name for dist in pulp_client.enumerate_distributions()}
        for remote in pulp_client.enumerate_remotes():
            (dist_dest_pattern, matched_source) = remote_expression.subn(
                args.distribution_dest_expression, remote.name)
            if matched_source:
                dist_dest_matches = [
                    dist for dist in distributions if re.match(dist_dest_pattern, dist)]
                if not dist_dest_matches:
                    print(
                        "No distributions match destination pattern '%s'" % dist_dest_pattern,
                        file=sys.stderr)
                    return 1
                dists_to_sync.extend((remote.name, dist_dest) for dist_dest in dist_dest_matches)

        dists_to_sync = sorted(set(dists_to_sync))
        print('Syncing %d distributions:' % len(dists_to_sync))
        for remote_name_and_dist_dest in dists_to_sync:
            print('- %s => %s' % remote_name_and_dist_dest)

    with Scope('SUBSECTION', 'synchronizing remotes and publishing mirrors'):
        for remote_name, dist_name in dists_to_sync:
            pulp_client.mirror_remote_to_distribution(remote_name, dist_name, dry_run=args.dry_run)


if __name__ == '__main__':
    sys.exit(main())
