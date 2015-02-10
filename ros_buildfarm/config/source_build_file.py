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

from .build_file import BuildFile


class SourceBuildFile(BuildFile):

    _type = 'source-build'

    def __init__(self, name, data):
        assert 'type' in data, "Expected file type is '%s'" % \
            SourceBuildFile._type
        assert data['type'] == SourceBuildFile._type, \
            "Expected file type is '%s', not '%s'" % \
            (SourceBuildFile._type, data['type'])

        assert 'version' in data, \
            "Source build file for '%s' lacks required version information" % \
            self.name
        assert int(data['version']) in [1, 2, 3], \
            ("Unable to handle '%s' format version '%d', please update " +
             "rosdistro (e.g. on Ubuntu/Debian use: sudo apt-get update && " +
             "sudo apt-get install --only-upgrade python-rosdistro)") % \
            (SourceBuildFile._type, int(data['version']))
        self.version = int(data['version'])

        super(SourceBuildFile, self).__init__(name, data)

        self.jenkins_commit_job_priority = None
        if 'jenkins_commit_job_priority' in data:
            self.jenkins_commit_job_priority = \
                int(data['jenkins_commit_job_priority'])
        self.jenkins_pull_request_job_priority = None
        if 'jenkins_pull_request_job_priority' in data:
            self.jenkins_pull_request_job_priority = \
                int(data['jenkins_pull_request_job_priority'])

        self.jenkins_job_label = None
        if 'jenkins_job_label' in data:
            self.jenkins_job_label = data['jenkins_job_label']
        self.jenkins_job_timeout = None
        if 'jenkins_job_timeout' in data:
            self.jenkins_job_timeout = int(data['jenkins_job_timeout'])

        self.notify_committers = None
        if 'notifications' in data:
            if 'committers' in data['notifications']:
                self.notify_committers = \
                    bool(data['notifications']['committers'])

        self.repository_blacklist = []
        if 'repository_blacklist' in data:
            self.repository_blacklist = data['repository_blacklist']
            assert isinstance(self.repository_blacklist, list)
        self.repository_whitelist = []
        if 'repository_whitelist' in data:
            self.repository_whitelist = data['repository_whitelist']
            assert isinstance(self.repository_whitelist, list)
        self.skip_ignored_repositories = None
        if 'skip_ignored_repositories' in data:
            self.skip_ignored_repositories = \
                bool(data['skip_ignored_repositories'])

        self.test_commits_default = False
        self.test_commits_force = None
        if 'test_commits' in data:
            if 'default' in data['test_commits']:
                    self.test_commits_default = bool(
                        data['test_commits']['default'])
            if 'force' in data['test_commits']:
                    self.test_commits_force = bool(
                        data['test_commits']['force'])

        self.test_pull_requests_default = False
        self.test_pull_requests_force = None
        if 'test_pull_requests' in data:
            if 'default' in data['test_pull_requests']:
                    self.test_pull_requests_default = bool(
                        data['test_pull_requests']['default'])
            if 'force' in data['test_pull_requests']:
                    self.test_pull_requests_force = bool(
                        data['test_pull_requests']['force'])

    def filter_repositories(self, repository_names):
        res = set(repository_names)
        if self.repository_whitelist:
            res &= set(self.repository_whitelist)
        res -= set(self.repository_blacklist)
        return res
