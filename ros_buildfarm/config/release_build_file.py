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

import copy


class ReleaseBuildFile(object):

    _type = 'release-build'

    def __init__(self, name, data):
        self.name = name

        assert 'type' in data, "Expected file type is '%s'" % ReleaseBuildFile._type
        assert data['type'] == ReleaseBuildFile._type, "Expected file type is '%s', not '%s'" % (ReleaseBuildFile._type, data['type'])

        assert 'version' in data, "Release build file for '%s' lacks required version information" % self.name
        assert int(data['version']) in [1, 2], "Unable to handle '%s' format version '%d', please update rosdistro (e.g. on Ubuntu/Debian use: sudo apt-get update && sudo apt-get install --only-upgrade python-rosdistro)" % (ReleaseBuildFile._type, int(data['version']))
        self.version = int(data['version'])

        self.abi_incompatibility_assumed = None
        if 'abi_incompatibility_assumed' in data and data['abi_incompatibility_assumed']:
            self.abi_incompatibility_assumed = True

        self.jenkins_binarydeb_job_timeout = None
        if 'jenkins_binarydeb_job_timeout' in data:
            self.jenkins_binarydeb_job_timeout = int(data['jenkins_binarydeb_job_timeout'])
        self.jenkins_job_priority = None
        if 'jenkins_job_priority' in data:
            self.jenkins_job_priority = int(data['jenkins_job_priority'])
        self.jenkins_sourcedeb_job_timeout = None
        if 'jenkins_sourcedeb_job_timeout' in data:
            self.jenkins_sourcedeb_job_timeout = int(data['jenkins_sourcedeb_job_timeout'])

        self.notify_committers = None
        self.notify_emails = []
        self.notify_maintainers = None
        if 'notifications' in data:
            if 'committers' in data['notifications'] and data['notifications']['committers']:
                self.notify_committers = True
            if 'emails' in data['notifications']:
                self.notify_emails = data['notifications']['emails']
                assert isinstance(self.notify_emails, list)
            if 'maintainers' in data['notifications'] and data['notifications']['maintainers']:
                self.notify_maintainers = True

        self.package_whitelist = []
        if 'package_whitelist' in data:
            self.package_whitelist = data['package_whitelist']
            assert isinstance(self.package_whitelist, list)
        self.package_blacklist = []
        if 'package_blacklist' in data:
            self.package_blacklist = data['package_blacklist']
            assert isinstance(self.package_blacklist, list)

        self.sync_package_count = None
        self.sync_packages = []
        if 'sync' in data:
            if 'package_count' in data['sync']:
                self.sync_package_count = int(data['sync']['package_count'])
            if 'packages' in data['sync']:
                self.sync_packages = data['sync']['packages']
                assert isinstance(self.sync_packages, list)

        self.repository_keys = []
        self.repository_urls = []
        if 'repositories' in data:
            if 'keys' in data['repositories']:
                self.repository_keys = data['repositories']['keys']
            if 'urls' in data['repositories']:
                self.repository_urls = data['repositories']['urls']
            assert len(self.repository_keys) == len(self.repository_urls)

        assert 'target_repository' in data
        self.target_repository = data['target_repository']

        assert 'targets' in data
        self.targets = {}
        for os_name in data['targets'].keys():
            self.targets[os_name] = {}
            for os_code_name in data['targets'][os_name]:
                self.targets[os_name][os_code_name] = {}
                for arch in data['targets'][os_name][os_code_name]:
                    self.targets[os_name][os_code_name][arch] = data['targets'][os_name][os_code_name][arch]

    def filter_packages(self, package_names):
        res = copy.copy(set(package_names))
        if self.package_whitelist:
            res &= set(self.package_whitelist)
        res -= set(self.package_blacklist)
        return res
