# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Open Source Robotics Foundation, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Open Source Robotics Foundation, Inc. nor
#    the names of its contributors may be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class Index(object):

    _type = 'buildfarm'

    def __init__(self, data, base_url):
        assert 'type' in data, "Expected file type is '%s'" % Index._type
        assert data['type'] == Index._type, \
            "Expected file type is '%s', not '%s'" % \
            (Index._type, data['type'])

        assert 'version' in data, \
            'Index file lacks required version information'
        # assert int(data['version']) > 1, \
        #     ("Unable to handle '%s' format version '%d' anymore, please " +
        #      "update your '%s' file to version '2'" %
        #      (Index._type, int(data['version']), Index._type)
        assert int(data['version']) in [1], \
            ("Unable to handle '%s' format version '%d', please update " +
             "ros_buildfarm") % (Index._type, int(data['version']))
        self.version = int(data['version'])

        self.distributions = {}
        if 'distributions' in data and data['distributions']:
            # if distributions is not a dict
            # raise an exception including the value
            # this can be used to notify users
            # (e.g. if an index.yaml file has been deleted / moved)
            if not isinstance(data['distributions'], dict):
                raise RuntimeError(
                    ("Distributions type is invalid: expected 'dict', but " +
                     "got '%s': %s") %
                    (type(data['distributions']).__name__,
                     data['distributions']))
            for distro_name in sorted(data['distributions']):
                self.distributions[distro_name] = {}
                distro_data = data['distributions'][distro_name]
                value_types = {
                    'doc_builds': dict,
                    'notification_emails': list,
                    'release_builds': dict,
                    'source_builds': dict,
                }
                for key in distro_data:
                    if key not in value_types.keys():
                        assert False, "unknown key '%s'" % key

                    value = distro_data[key]
                    if not isinstance(value, value_types[key]):
                        assert False, \
                            "wrong type of key '%s': %s" % (key, type(value))

                    if isinstance(value, dict):
                        self.distributions[distro_name][key] = {}
                        for k, v in value.items():
                            v = _resolve_url(base_url, v)
                            self.distributions[distro_name][key][k] = v
                    elif isinstance(value, list):
                        self.distributions[distro_name][key] = []
                        for v in value:
                            self.distributions[distro_name][key].append(v)
                    else:
                        assert False

                unset_keys = [
                    k for k in value_types.keys()
                    if k not in distro_data]
                for key in unset_keys:
                    self.distributions[distro_name][key] = value_types[key]()

        self.doc_builds = {}
        if 'doc_builds' in data and data['doc_builds']:
            assert isinstance(data['doc_builds'], dict)
            for k, v in data['doc_builds'].items():
                v = _resolve_url(base_url, v)
                self.doc_builds[k] = v

        self.jenkins_url = data['jenkins_url']

        self.notify_emails = []
        if 'notification_emails' in data:
            self.notify_emails = data['notification_emails']
            assert isinstance(self.notify_emails, list)

        self.prerequisites = data['prerequisites']

        self.rosdistro_index_url = data['rosdistro_index_url']

        self.status_page_repositories = {}
        if 'status_page_repositories' in data:
            assert isinstance(data['status_page_repositories'], dict)
            for status_page_name, repo_urls in \
                    data['status_page_repositories'].items():
                assert isinstance(repo_urls, list)
                self.status_page_repositories[status_page_name] = repo_urls


def _resolve_url(base_url, value):
    parts = urlparse(value)
    if not parts[0]:  # schema
        value = base_url + '/' + value
    return value
