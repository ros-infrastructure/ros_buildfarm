# Copyright 2014 Open Source Robotics Foundation, Inc.
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

import logging
import os

from .common import PlatformPackageDescriptor
from .http_cache import fetch_and_cache_gzip


def get_debian_repo_index(debian_repository_baseurl, target, cache_dir):
    url = os.path.join(
        debian_repository_baseurl, 'dists', target.os_code_name, 'main')
    if target.arch == 'source':
        url = os.path.join(url, 'source', 'Sources.gz')
    else:
        url = os.path.join(url, 'binary-%s' % target.arch, 'Packages.gz')

    cache_filename = fetch_and_cache_gzip(url, cache_dir)

    logging.debug('Reading file: %s' % cache_filename)
    # split package blocks
    with open(cache_filename, 'rb') as f:
        blocks = f.read().decode('utf8').split('\n\n')
    blocks = [b.splitlines() for b in blocks if b]

    # extract version number of every package
    package_versions = {}
    for lines in blocks:
        prefix = 'Package: '
        assert lines[0].startswith(prefix)
        debian_pkg_name = lines[0][len(prefix):]

        prefix = 'Version: '
        versions = [line[len(prefix):] for line in lines if line.startswith(prefix)]
        version = versions[0] if len(versions) == 1 else None

        prefix = 'Source: '
        source_names = [line[len(prefix):] for line in lines if line.startswith(prefix)]
        source_name = source_names[0] if len(source_names) == 1 else None

        package_versions[debian_pkg_name] = PlatformPackageDescriptor(version, source_name)

    return package_versions
