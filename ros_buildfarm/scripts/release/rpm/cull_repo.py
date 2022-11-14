# Copyright 2022 Open Source Robotics Foundation, Inc.
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
import logging
import sys

from ros_buildfarm.argument import add_argument_dry_run
from ros_buildfarm.argument import add_argument_pulp_base_url
from ros_buildfarm.argument import add_argument_pulp_distribution_name
from ros_buildfarm.argument import add_argument_pulp_password
from ros_buildfarm.argument import add_argument_pulp_task_timeout
from ros_buildfarm.argument import add_argument_pulp_username
from ros_buildfarm.common import Scope
from ros_buildfarm.pulp import PulpRpmClient


def main(argv=sys.argv[1:]):
    logging.basicConfig(
        level=logging.DEBUG, format='%(name)s %(levelname)s %(asctime)s: %(message)s')

    parser = argparse.ArgumentParser(
        description='Cull unused repository snapshots and packages from Pulp')
    add_argument_dry_run(parser)
    add_argument_pulp_base_url(parser)
    add_argument_pulp_distribution_name(parser)
    add_argument_pulp_password(parser)
    add_argument_pulp_task_timeout(parser)
    add_argument_pulp_username(parser)
    args = parser.parse_args(argv)

    pulp_client = PulpRpmClient(
        args.pulp_base_url, args.pulp_username, args.pulp_password,
        task_timeout=args.pulp_task_timeout)

    with Scope('SUBSECTION', 'removing unused snapshots'):
        pulp_client.remove_unused_repo_vers(args.pulp_distribution_name, dry_run=args.dry_run)

    with Scope('SUBSECTION', 'removing unused content'):
        if args.dry_run:
            print('Skipped (dry-run)')
        else:
            pulp_client.remove_unused_content()


if __name__ == '__main__':
    sys.exit(main())
