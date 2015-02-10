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


class ReleaseBuildFile(BuildFile):

    _type = 'release-build'

    def __init__(self, name, data):
        assert 'type' in data, \
            "Expected file type is '%s'" % ReleaseBuildFile._type
        assert data['type'] == ReleaseBuildFile._type, \
            "Expected file type is '%s', not '%s'" % \
            (ReleaseBuildFile._type, data['type'])

        assert 'version' in data, \
            ("Release build file for '%s' lacks required version " +
             "information") % self.name
        assert int(data['version']) in [1, 2], \
            ("Unable to handle '%s' format version '%d', please update " +
             "rosdistro (e.g. on Ubuntu/Debian use: sudo apt-get update && " +
             "sudo apt-get install --only-upgrade python-rosdistro)") % \
            (ReleaseBuildFile._type, int(data['version']))
        self.version = int(data['version'])

        super(ReleaseBuildFile, self).__init__(name, data)

        self.abi_incompatibility_assumed = None
        if 'abi_incompatibility_assumed' in data:
            self.abi_incompatibility_assumed = \
                bool(data['abi_incompatibility_assumed'])

        self.jenkins_binary_job_label = None
        if 'jenkins_binary_job_label' in data:
            self.jenkins_binary_job_label = data['jenkins_binary_job_label']
        self.jenkins_binary_job_priority = None
        if 'jenkins_binary_job_priority' in data:
            self.jenkins_binary_job_priority = \
                int(data['jenkins_binary_job_priority'])
        self.jenkins_binary_job_timeout = None
        if 'jenkins_binary_job_timeout' in data:
            self.jenkins_binary_job_timeout = \
                int(data['jenkins_binary_job_timeout'])

        self.jenkins_source_job_label = None
        if 'jenkins_source_job_label' in data:
            self.jenkins_source_job_label = data['jenkins_source_job_label']
        self.jenkins_source_job_priority = None
        if 'jenkins_source_job_priority' in data:
            self.jenkins_source_job_priority = \
                int(data['jenkins_source_job_priority'])
        self.jenkins_source_job_timeout = None
        if 'jenkins_source_job_timeout' in data:
            self.jenkins_source_job_timeout = \
                int(data['jenkins_source_job_timeout'])

        self.package_whitelist = []
        if 'package_whitelist' in data:
            self.package_whitelist = data['package_whitelist']
            assert isinstance(self.package_whitelist, list)
        self.package_blacklist = []
        if 'package_blacklist' in data:
            self.package_blacklist = data['package_blacklist']
            assert isinstance(self.package_blacklist, list)
        self.skip_ignored_packages = None
        if 'skip_ignored_packages' in data:
            self.skip_ignored_packages = \
                bool(data['skip_ignored_packages'])

        self.sync_package_count = None
        self.sync_packages = []
        if 'sync' in data:
            if 'package_count' in data['sync']:
                self.sync_package_count = int(data['sync']['package_count'])
            if 'packages' in data['sync']:
                self.sync_packages = data['sync']['packages']
                assert isinstance(self.sync_packages, list)

        assert 'target_repository' in data
        self.target_repository = data['target_repository']

        assert 'upload_credential_id' in data
        self.upload_credential_id = data['upload_credential_id']

    def filter_packages(self, package_names):
        res = set(package_names)
        if self.package_whitelist:
            res &= set(self.package_whitelist)
        res -= set(self.package_blacklist)
        return res
