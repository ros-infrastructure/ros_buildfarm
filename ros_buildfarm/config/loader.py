# Copyright 2013-2014, 2016 Open Source Robotics Foundation, Inc.
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

import socket
import time
import os
import sys
import base64

try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
    from urllib.error import URLError
except ImportError:
    from urllib2 import urlopen, Request
    from urllib2 import HTTPError
    from urllib2 import URLError


GITHUB_USER = os.getenv('GITHUB_USER', None)
GITHUB_PASSWORD = os.getenv('GITHUB_PASSWORD', None)


def auth_header(username=None, password=None, token=None):
    if username and password:
        if sys.version_info > (3, 0):
            userandpass = base64.b64encode(bytes('%s:%s' % (username, password), 'utf-8'))
        else:
            userandpass = base64.b64encode('%s:%s' % (username, password))
        userandpass = userandpass.decode('ascii')
        return 'Basic %s' % userandpass
    elif token:
        return 'token %s' % token


def load_url(url, retry=2, retry_period=1, timeout=10, skip_decode=False):
    req = Request(url)
    if GITHUB_USER and GITHUB_PASSWORD:
        authheader = auth_header(username=GITHUB_USER, password=GITHUB_PASSWORD)
        req.add_header('Authorization', authheader)
    try:
        fh = urlopen(req, timeout=timeout)
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
    except socket.timeout as e:
        if retry:
            time.sleep(retry_period)
            return load_url(
                url, retry=retry - 1, retry_period=retry_period,
                timeout=timeout)
        raise socket.timeout(str(e) + ' (%s)' % url)
    # Python 2/3 Compatibility
    contents = fh.read()
    if isinstance(contents, str) or skip_decode:
        return contents
    else:
        return contents.decode('utf-8')
