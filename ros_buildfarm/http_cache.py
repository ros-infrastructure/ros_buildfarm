# Copyright 2014, 2020 Open Source Robotics Foundation, Inc.
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
try:
    from urllib.error import HTTPError
    from urllib.error import URLError
    from urllib.request import urlopen
except ImportError:
    from urllib2 import HTTPError
    from urllib2 import URLError
    from urllib2 import urlopen


def fetch_and_cache_gzip(url, cache_dir):
    cache_filename = os.path.join(
        cache_dir, hashlib.md5(url.encode()).hexdigest())
    if not os.path.exists(cache_filename):
        _fetch_gzip_url(url, cache_filename)
    return cache_filename


def fetch_and_cache_plaintext(url, cache_dir):
    cache_filename = os.path.join(
        cache_dir, hashlib.md5(url.encode()).hexdigest())
    if not os.path.exists(cache_filename):
        _fetch_plain_url(url, cache_filename)
    return cache_filename


def _fetch_gzip_url(url, dst_filename):
    dst_dirname = os.path.dirname(dst_filename)
    if not os.path.exists(dst_dirname):
        os.makedirs(dst_dirname)
    logging.debug('Downloading gz url: %s' % url)
    gz_str = _load_url(url)
    gz_stream = BytesIO(gz_str)
    g = GzipFile(fileobj=gz_stream, mode='rb')
    with open(dst_filename, 'wb') as f:
        f.write(g.read())


def _fetch_plain_url(url, dst_filename):
    dst_dirname = os.path.dirname(dst_filename)
    if not os.path.exists(dst_dirname):
        os.makedirs(dst_dirname)
    logging.debug('Downloading url: %s' % url)
    with open(dst_filename, 'wb') as f:
        f.write(_load_url(url))


def _load_url(url, retry=2, retry_period=1, timeout=10):
    try:
        fh = urlopen(url, timeout=timeout)
    except HTTPError as e:
        if e.code == 503 and retry:
            time.sleep(retry_period)
            return _load_url(
                url, retry=retry - 1, retry_period=retry_period,
                timeout=timeout)
        e.msg += ' (%s)' % url
        raise
    except URLError as e:
        if isinstance(e.reason, socket.timeout) and retry:
            time.sleep(retry_period)
            return _load_url(
                url, retry=retry - 1, retry_period=retry_period,
                timeout=timeout)
        raise URLError(str(e) + ' (%s)' % url)
    return fh.read()
