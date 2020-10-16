#!/usr/bin/env python3

# Copyright 2014-2016 Open Source Robotics Foundation, Inc.
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

import argparse
import copy
import sys

from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_dry_run
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import get_release_job_prefix
from ros_buildfarm.config import get_index
from ros_buildfarm.config import get_release_build_files
from ros_buildfarm.git import get_repository
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_management_view
from ros_buildfarm.jenkins import connect
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'repos_status_page' job on Jenkins")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_dry_run(parser)
    args = parser.parse_args(argv)

    config = get_index(args.config_url)
    job_config = get_job_config(args, config)

    jenkins = connect(config.jenkins_url)

    configure_management_view(jenkins, dry_run=args.dry_run)

    prefix = get_release_job_prefix(args.rosdistro_name)
    job_name = '%s_repos-status-page' % prefix
    configure_job(jenkins, job_name, job_config, dry_run=args.dry_run)


def get_job_config(args, config):
    template_name = 'status/repos_status_page_job.xml.em'

    targets_by_repo = get_targets_by_repo(config, args.rosdistro_name)
    status_pages = {}
    for name, repo_urls in config.status_page_repositories.items():
        data = get_status_page_data(repo_urls, targets_by_repo)
        if data is not None:
            status_pages[name] = data
        else:
            print(("Skipping repos status page '%s' since no repository URLs " +
                   'match any of the release build files') % name)

    job_data = copy.deepcopy(args.__dict__)
    job_data.update({
        'ros_buildfarm_repository': get_repository(),

        'status_pages': status_pages,

        'notification_emails':
        config.distributions[args.rosdistro_name]['notification_emails'],
    })
    job_config = expand_template(template_name, job_data)
    return job_config


def get_targets_by_repo(config, ros_distro_name):
    # collect all target repositories (building) and their targets
    # from all release build files
    target_dicts_by_repo = {}
    release_build_files = get_release_build_files(config, ros_distro_name)
    for release_build_file in release_build_files.values():
        target_repository = release_build_file.target_repository
        merged_os_names = target_dicts_by_repo.setdefault(
            target_repository, {})
        for os_name in release_build_file.targets.keys():
            os_code_names = release_build_file.targets[os_name]
            merged_os_code_names = merged_os_names.setdefault(os_name, {})
            for os_code_name in os_code_names.keys():
                arches = os_code_names[os_code_name]
                merged_arches = merged_os_code_names.setdefault(
                    os_code_name, {})
                for arch in arches.keys():
                    merged_arches.setdefault(arch, {})

    # flatten each os_code_name and arch into a single colon separated string
    targets_by_repo = {}
    for target_repository in target_dicts_by_repo.keys():
        targets_by_repo[target_repository] = []
        targets = target_dicts_by_repo[target_repository]
        # TODO support other OS names
        for os_name in ['debian', 'fedora', 'rhel', 'ubuntu']:
            if os_name not in targets:
                continue
            for os_code_name in sorted(targets[os_name].keys()):
                target = '%s:%s:source' % (os_name, os_code_name)
                targets_by_repo[target_repository].append(target)
                for arch in sorted(targets[os_name][os_code_name].keys()):
                    target = '%s:%s:%s' % (os_name, os_code_name, arch)
                    targets_by_repo[target_repository].append(target)
    return targets_by_repo


def get_status_page_data(repo_urls, targets_by_repo):
    targets = None
    for repo_url in repo_urls:
        if repo_url in targets_by_repo.keys():
            targets = targets_by_repo[repo_url]
            break
    if targets is None:
        return None

    data = {}
    data['debian_repository_urls'] = repo_urls
    data['os_name_and_os_code_name_and_arch_tuples'] = targets
    return data


if __name__ == '__main__':
    main()
