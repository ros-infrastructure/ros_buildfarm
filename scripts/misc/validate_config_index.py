#!/usr/bin/env python3

# Copyright 2021 Open Source Robotics Foundation, Inc.
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
        description="Parse and validate a buildfarm configuration")
    add_argument_config_url(parser)
    args = parser.parse_args(argv)

    print('Loading index...')
    index = get_index(args.config_url)

    for dist_name in index.distributions.keys():
        print('Processing distrubiton: ' + dist_name)
        configs = get_ci_build_files(index, dist_name)
        print('- Processed %d ci configs' % (len(configs),))
        configs = get_doc_build_files(index, dist_name)
        print('- Processed %d doc configs' % (len(configs),))
        configs = get_release_build_files(index, dist_name)
        print('- Processed %d release configs' % (len(configs),))
        configs = get_source_build_files(index, dist_name)
        print('- Processed %d source configs' % (len(configs),))

    configs = get_global_doc_build_files(index)
    print('Processed %d global doc configs' % (len(configs),))


if __name__ == '__main__':
    main()
