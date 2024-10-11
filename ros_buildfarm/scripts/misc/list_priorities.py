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
import sys

from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.config import (
    get_ci_build_files,
    get_doc_build_files,
    get_global_doc_build_files,
    get_index,
    get_release_build_files,
    get_source_build_files,
)


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Print Jenkins job priority for all configured jobs")
    add_argument_config_url(parser)
    args = parser.parse_args(argv)

    index = get_index(args.config_url)

    priorities = {}
    for dist_name in index.distributions.keys():
        _process_priorities(priorities, get_ci_build_files(index, dist_name))
        _process_priorities(priorities, get_doc_build_files(index, dist_name))
        _process_priorities(priorities, get_release_build_files(index, dist_name))
        _process_priorities(priorities, get_source_build_files(index, dist_name))

    _process_priorities(priorities, get_global_doc_build_files(index))

    for priority, jobs in sorted(priorities.items()):
        print(priority)
        for key, name in sorted(jobs):
            print('  %s::%s' % (key, name))


def _process_priorities(priorities, configs):
    for config in configs.values():
        for k, v in config.__dict__.items():
            if k.endswith('_priority'):
                priority = getattr(config, k)
                priorities.setdefault(priority, set())
                priorities[priority].add((k, config.url))


if __name__ == '__main__':
    sys.exit(main())
