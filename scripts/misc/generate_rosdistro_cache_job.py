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
from ros_buildfarm.common import get_devel_view_name
from ros_buildfarm.common import get_doc_view_name
from ros_buildfarm.common import get_release_job_prefix
from ros_buildfarm.common import \
    get_repositories_and_script_generating_key_files
from ros_buildfarm.config import get_doc_build_files
from ros_buildfarm.config import get_index
from ros_buildfarm.config import get_release_build_files
from ros_buildfarm.config import get_source_build_files
from ros_buildfarm.git import get_repository
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_management_view
from ros_buildfarm.jenkins import connect
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'dashboard' job on Jenkins")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_dry_run(parser)
    args = parser.parse_args(argv)

    config = get_index(args.config_url)
    job_config = get_job_config(args, config)

    jenkins = connect(config.jenkins_url)

    configure_management_view(jenkins, dry_run=args.dry_run)

    job_name = '%s_rosdistro-cache' % args.rosdistro_name
    configure_job(jenkins, job_name, job_config, dry_run=args.dry_run)


def get_job_config(args, config):
    template_name = 'misc/rosdistro_cache_job.xml.em'

    repository_args, script_generating_key_files = \
        get_repositories_and_script_generating_key_files(config=config)

    reconfigure_job_names = []
    build_files = get_release_build_files(config, args.rosdistro_name)
    for release_build_name in sorted(build_files.keys()):
        group_name = get_release_job_prefix(
            args.rosdistro_name, release_build_name)
        job_name = '%s_%s' % (group_name, 'reconfigure-jobs')
        reconfigure_job_names.append(job_name)

    reconfigure_doc_job_names = []
    build_files = get_doc_build_files(config, args.rosdistro_name)
    for doc_build_name in sorted(build_files.keys()):
        group_name = get_doc_view_name(
            args.rosdistro_name, doc_build_name)
        job_name = '%s_%s' % (group_name, 'reconfigure-jobs')
        reconfigure_doc_job_names.append(job_name)

    reconfigure_source_job_names = []
    build_files = get_source_build_files(config, args.rosdistro_name)
    for source_build_name in sorted(build_files.keys()):
        group_name = get_devel_view_name(
            args.rosdistro_name, source_build_name)
        job_name = '%s_%s' % (group_name, 'reconfigure-jobs')
        reconfigure_source_job_names.append(job_name)

    job_data = copy.deepcopy(args.__dict__)
    job_data.update({
        'ros_buildfarm_repository': get_repository(),

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_index_url': config.rosdistro_index_url,

        'repository_args': repository_args,

        'reconfigure_job_names': reconfigure_job_names,
        'reconfigure_doc_job_names': reconfigure_doc_job_names,
        'reconfigure_source_job_names': reconfigure_source_job_names,

        'notification_emails':
        config.distributions[args.rosdistro_name]['notification_emails'],

        'git_ssh_credential_id': config.git_ssh_credential_id,
    })
    job_config = expand_template(template_name, job_data)
    return job_config


if __name__ == '__main__':
    main()
