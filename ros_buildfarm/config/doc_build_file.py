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

DOC_TYPE_ROSDOC = 'rosdoc_lite'
DOC_TYPE_MANIFEST = 'released_manifest'
DOC_TYPE_MAKE = 'make_target'
DOC_TYPES = [DOC_TYPE_ROSDOC, DOC_TYPE_MANIFEST, DOC_TYPE_MAKE]


class DocBuildFile(BuildFile):

    _type = 'doc-build'

    def __init__(self, name, data):
        assert 'type' in data, \
            "Expected file type is '%s'" % DocBuildFile._type
        assert data['type'] == DocBuildFile._type, \
            "Expected file type is '%s', not '%s'" % \
            (DocBuildFile._type, data['type'])

        assert 'version' in data, \
            "Doc build file for '%s' lacks required version information" % \
            self.name
        assert int(data['version']) in [1, 2], \
            ("Unable to handle '%s' format version '%d', please update " +
             "rosdistro (e.g. on Ubuntu/Debian use: sudo apt-get update && " +
             "sudo apt-get install --only-upgrade python-rosdistro)") % \
            (DocBuildFile._type, int(data['version']))
        self.version = int(data['version'])

        super(DocBuildFile, self).__init__(name, data)

        # ensure that a single target is specified
        assert len(self.targets) == 1
        os_name = list(self.targets.keys())[0]
        assert len(self.targets[os_name]) == 1
        os_code_name = list(self.targets[os_name].keys())[0]
        assert len(self.targets[os_name][os_code_name]) == 1

        self.documentation_type = DOC_TYPE_ROSDOC
        if 'documentation_type' in data:
            assert data['documentation_type'] in DOC_TYPES, \
                ("Doc build file for '%s' has unknown documentation type " +
                 "'%s'") % (self.name, data['documentation_type'])
            self.documentation_type = data['documentation_type']

        # repository keys and urls can only be used with doc type rosdoc
        is_rosdoc_type = self.documentation_type == DOC_TYPE_ROSDOC
        assert not self.repository_keys or is_rosdoc_type
        assert not self.repository_urls or is_rosdoc_type

        self.canonical_base_url = None
        if 'canonical_base_url' in data:
            self.canonical_base_url = data['canonical_base_url']
            assert not self.canonical_base_url or is_rosdoc_type

        self.doc_repositories = []
        if 'doc_repositories' in data:
            self.doc_repositories = data['doc_repositories']
            assert isinstance(self.doc_repositories, list)

        # doc_repositories can only be used with doc type make_target
        is_make_target_type = self.documentation_type == DOC_TYPE_MAKE
        assert not self.doc_repositories or is_make_target_type

        self.jenkins_job_label = None
        if 'jenkins_job_label' in data:
            self.jenkins_job_label = data['jenkins_job_label']
        self.jenkins_job_priority = None
        if 'jenkins_job_priority' in data:
            self.jenkins_job_priority = int(data['jenkins_job_priority'])
        self.jenkins_job_timeout = None
        if 'jenkins_job_timeout' in data:
            self.jenkins_job_timeout = int(data['jenkins_job_timeout'])

        self.notify_committers = None
        if 'notifications' in data:
            if 'committers' in data['notifications']:
                self.notify_committers = \
                    bool(data['notifications']['committers'])

        # notify committers/maintainers can only be used with doc type rosdoc
        assert not self.notify_committers or is_rosdoc_type
        assert not self.notify_maintainers or is_rosdoc_type

        self.package_blacklist = []
        if 'package_blacklist' in data:
            self.package_blacklist = data['package_blacklist']
            assert isinstance(self.package_blacklist, list)
        self.package_whitelist = []
        if 'package_whitelist' in data:
            self.package_whitelist = data['package_whitelist']
            assert isinstance(self.package_whitelist, list)

        # package black-/whitelist can only be used with doc type manifest
        is_manifest_type = self.documentation_type == DOC_TYPE_MANIFEST
        assert not self.package_blacklist or is_manifest_type
        assert not self.package_whitelist or is_manifest_type

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

        # repository black-/whitelist can only be used with doc type rosdoc
        assert not self.repository_blacklist or is_rosdoc_type
        assert not self.repository_whitelist or is_rosdoc_type
        assert self.skip_ignored_repositories is None or is_rosdoc_type
        assert 'upload_credential_id' in data
        self.upload_credential_id = data['upload_credential_id']

    def filter_packages(self, package_names):
        res = set(package_names)
        if self.package_whitelist:
            res &= set(self.package_whitelist)
        res -= set(self.package_blacklist)
        return res

    def filter_repositories(self, repository_names):
        res = set(repository_names)
        if self.repository_whitelist:
            res &= set(self.repository_whitelist)
        res -= set(self.repository_blacklist)
        return res
