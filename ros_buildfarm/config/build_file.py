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


class BuildFile(object):

    def __init__(self, name, data):
        self.name = name

        self.notify_emails = []
        self.notify_maintainers = None
        if 'notifications' in data:
            if 'emails' in data['notifications']:
                self.notify_emails = data['notifications']['emails']
                assert isinstance(self.notify_emails, list)
            if 'maintainers' in data['notifications'] and \
                    data['notifications']['maintainers']:
                self.notify_maintainers = True

        self.repository_keys = []
        self.repository_urls = []
        if 'repositories' in data:
            if 'keys' in data['repositories']:
                self.repository_keys = data['repositories']['keys']
                assert isinstance(self.repository_keys, list)
            if 'urls' in data['repositories']:
                self.repository_urls = data['repositories']['urls']
                assert isinstance(self.repository_urls, list)
            assert len(self.repository_keys) == len(self.repository_urls)

        self.tag_whitelist = []
        self.tag_blacklist = []
        if 'tag_whitelist' in data:
            self.tag_whitelist = data['tag_whitelist']
            assert isinstance(self.tag_whitelist, list)
        if 'tag_blacklist' in data:
            self.tag_blacklist = data['tag_blacklist']
            assert isinstance(self.tag_blacklist, list)

        assert 'targets' in data
        self.targets = {}
        for os_name in data['targets'].keys():
            self.targets[os_name] = {}
            for os_code_name in data['targets'][os_name].keys():
                self.targets[os_name][os_code_name] = {}
                for arch in data['targets'][os_name][os_code_name].keys():
                    self.targets[os_name][os_code_name][arch] = \
                        data['targets'][os_name][os_code_name][arch]

    def filter_distribution_files_by_tags(self, dist_files):
        res = []

        def match_distribution_file_tags(tags, whitelist, blacklist):
            # check if any tag matches the blacklist
            for tag in blacklist:
                if tag in tags:
                    return False
            # check if any tag matches the whitelist
            if whitelist:
                for tag in whitelist:
                    if tag in tags:
                        return True
            # if no tag matched any of the lists
            # the result depends on if a whitelist was specified
            return not whitelist

        for dist_file in dist_files:
            if match_distribution_file_tags(
                    dist_file.tags, self.tag_whitelist, self.tag_blacklist):
                res.append(dist_file)

        return res
