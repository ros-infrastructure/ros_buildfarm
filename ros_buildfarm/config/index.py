# Copyright 2013-2015 Open Source Robotics Foundation, Inc.
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

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class Index(object):

    _type = 'buildfarm'

    def __init__(self, data, base_url):  # noqa: D107
        assert 'type' in data, "Expected file type is '%s'" % Index._type
        assert data['type'] == Index._type, \
            "Expected file type is '%s', not '%s' loaded from '%s'" % \
            (Index._type, data['type'], base_url)

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
                    'ci_builds': dict,
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
                    elif isinstance(value, int):
                        self.distributions[distro_name][key] = value
                    else:
                        assert False

                unset_keys = [
                    k for k in value_types.keys()
                    if k not in self.distributions[distro_name]]
                for key in unset_keys:
                    self.distributions[distro_name][key] = value_types[key]()

        self.ci_builds = {}
        if 'ci_builds' in data and data['ci_builds']:
            assert isinstance(data['ci_builds'], dict)
            for k, v in data['ci_builds'].items():
                v = _resolve_url(base_url, v)
                self.ci_builds[k] = v

        self.doc_builds = {}
        if 'doc_builds' in data and data['doc_builds']:
            assert isinstance(data['doc_builds'], dict)
            for k, v in data['doc_builds'].items():
                v = _resolve_url(base_url, v)
                self.doc_builds[k] = v

        self.git_ssh_credential_id = ''
        if 'git_ssh_credential_id' in data:
            self.git_ssh_credential_id = data['git_ssh_credential_id']
            assert isinstance(self.git_ssh_credential_id, str)

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
