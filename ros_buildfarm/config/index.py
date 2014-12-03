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
        assert data['type'] == Index._type, "Expected file type is '%s', not '%s'" % (Index._type, data['type'])

        assert 'version' in data, 'Index file lacks required version information'
        #assert int(data['version']) > 1, "Unable to handle '%s' format version '%d' anymore, please update your '%s' file to version '2'" % (Index._type, int(data['version']), Index._type)
        #assert int(data['version']) in [2, 3], "Unable to handle '%s' format version '%d', please update rosdistro (e.g. on Ubuntu/Debian use: sudo apt-get update && sudo apt-get install --only-upgrade python-rosdistro)" % (Index._type, int(data['version']))
        self.version = int(data['version'])

        self.distributions = {}
        if 'distributions' in data and data['distributions']:
            # if distributions is not a dict raise an exception including the value
            # this can be used to notify users (e.g. if an index.yaml file has been deleted / moved)
            if not isinstance(data['distributions'], dict):
                raise RuntimeError("Distributions type is invalid: expected 'dict', but got '%s': %s" % (type(data['distributions']).__name__, data['distributions']))
            for distro_name in sorted(data['distributions']):
                self.distributions[distro_name] = {}
                distro_data = data['distributions'][distro_name]
                for key in distro_data:
                    if key not in ['release_builds', 'source_builds', 'doc_builds']:
                        assert False, "unknown key '%s'" % key

                    value = distro_data[key]
                    if not isinstance(value, dict):
                        assert False, "wrong type of key '%s': %s" % (key, type(value))

                    def resolve_url(base_url, value):
                        parts = urlparse(value)
                        if not parts[0]:  # schema
                            value = base_url + '/' + value
                        return value

                    self.distributions[distro_name][key] = {}
                    for k, v in value.items():
                        v = resolve_url(base_url, v)
                        self.distributions[distro_name][key][k] = v

        self.jenkins_url = data['jenkins_url']

        self.notify_emails = []
        if 'notifications' in data:
            if 'notification_emails' in data:
                self.notify_emails = data['notification_emails']
                assert isinstance(self.notify_emails, list)

        self.prerequisites = data['prerequisites']

        self.rosdistro_index_url = data['rosdistro_index_url']
        self.ros_buildfarm_repo = data['ros_buildfarm_repo']
