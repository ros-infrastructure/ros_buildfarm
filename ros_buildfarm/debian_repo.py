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

from gzip import GzipFile
import hashlib
from io import BytesIO
import logging
import os
import socket
import time
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import urlopen


def get_debian_repo_data(debian_repository_baseurl, targets, cache_dir):
    data = {}
    for target in targets:
        index = get_debian_repo_index(
            debian_repository_baseurl, target, cache_dir)
        data[target] = index
    return data


def get_debian_repo_index(debian_repository_baseurl, target, cache_dir):
    url = os.path.join(
        debian_repository_baseurl, 'dists', target.os_code_name, 'main')
    if target.arch == 'source':
        url = os.path.join(url, 'source', 'Sources.gz')
    else:
        url = os.path.join(url, 'binary-%s' % target.arch, 'Packages.gz')

    cache_filename = os.path.join(
        cache_dir, hashlib.md5(url.encode()).hexdigest())
    if not os.path.exists(cache_filename):
        fetch_gzip_url(url, cache_filename)

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
        versions = [l[len(prefix):] for l in lines if l.startswith(prefix)]
        version = versions[0] if len(versions) == 1 else None

        package_versions[debian_pkg_name] = version

    return package_versions


def fetch_gzip_url(url, dst_filename):
    dst_dirname = os.path.dirname(dst_filename)
    if not os.path.exists(dst_dirname):
        os.makedirs(dst_dirname)
    logging.debug('Downloading gz url: %s' % url)
    gz_str = load_url(url)
    gz_stream = BytesIO(gz_str)
    g = GzipFile(fileobj=gz_stream, mode='rb')
    with open(dst_filename, 'wb') as f:
        f.write(g.read())


def load_url(url, retry=2, retry_period=1, timeout=10):
    try:
        fh = urlopen(url, timeout=timeout)
    except HTTPError as e:
        if e.code == 503 and retry:
            time.sleep(retry_period)
            return load_url(
                url, retry=retry - 1, retry_period=retry_period,
                timeout=timeout)
        e.msg += ' (%s)' % url
        raise
    except URLError as e:
        if isinstance(e.reason, socket.timeout) and retry:
            time.sleep(retry_period)
            return load_url(
                url, retry=retry - 1, retry_period=retry_period,
                timeout=timeout)
        raise URLError(str(e) + ' (%s)' % url)
    return fh.read()
