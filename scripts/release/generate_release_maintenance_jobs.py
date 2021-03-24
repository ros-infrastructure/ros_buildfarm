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
import os
import sys

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_dry_run
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import get_release_binary_view_prefix
from ros_buildfarm.common import get_release_job_prefix
from ros_buildfarm.common import get_release_source_view_prefix
from ros_buildfarm.common import \
    get_repositories_and_script_generating_key_files
from ros_buildfarm.common import package_format_mapping
from ros_buildfarm.config import get_index
from ros_buildfarm.config import get_release_build_files
from ros_buildfarm.git import get_repository
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_management_view
from ros_buildfarm.jenkins import connect
from ros_buildfarm.jenkins_credentials import get_relative_credential_path
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'release' management jobs on Jenkins")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'release')
    add_argument_dry_run(parser)
    args = parser.parse_args(argv)

    config = get_index(args.config_url)
    build_files = get_release_build_files(config, args.rosdistro_name)
    build_file = build_files[args.release_build_name]

    package_formats = set(
        package_format_mapping[os_name] for os_name in build_file.targets.keys())
    assert len(package_formats) == 1
    package_format = package_formats.pop()

    group_name = get_release_job_prefix(
        args.rosdistro_name, args.release_build_name)

    reconfigure_jobs_job_config = get_reconfigure_jobs_job_config(
        args, config, build_file)
    trigger_jobs_job_config = get_trigger_jobs_job_config(
        args, config, build_file)
    trigger_missed_jobs_job_config = get_trigger_missed_jobs_job_config(
        args, config, build_file)
    import_upstream_job_config = get_import_upstream_job_config(
        args, config, build_file, package_format)
    trigger_broken_with_non_broken_upstream_job_config = \
        _get_trigger_broken_with_non_broken_upstream_job_config(
            args.rosdistro_name, args.release_build_name, build_file)

    jenkins = connect(config.jenkins_url)

    configure_management_view(jenkins, dry_run=args.dry_run)

    job_name = '%s_%s' % (group_name, 'reconfigure-jobs')
    configure_job(
        jenkins, job_name, reconfigure_jobs_job_config, dry_run=args.dry_run)

    job_name = '%s_%s' % (group_name, 'trigger-jobs')
    configure_job(
        jenkins, job_name, trigger_jobs_job_config, dry_run=args.dry_run)

    job_name = '%s_%s' % (group_name, 'trigger-missed-jobs')
    configure_job(
        jenkins, job_name, trigger_missed_jobs_job_config,
        dry_run=args.dry_run)

    job_name = 'import_upstream%s' % ('' if package_format == 'deb' else '_' + package_format)
    configure_job(
        jenkins, job_name, import_upstream_job_config, dry_run=args.dry_run)

    job_name = '%s_%s' % \
        (group_name, 'trigger-broken-with-non-broken-upstream')
    configure_job(
        jenkins, job_name, trigger_broken_with_non_broken_upstream_job_config,
        dry_run=args.dry_run)


def get_reconfigure_jobs_job_config(args, config, build_file):
    template_name = 'release/release_reconfigure-jobs_job.xml.em'
    return _get_job_config(
        args, config, build_file.notify_emails, template_name)


def get_trigger_jobs_job_config(args, config, build_file):
    template_name = 'release/release_trigger-jobs_job.xml.em'
    data = {'missed_jobs': False}
    return _get_job_config(
        args, config, build_file.notify_emails, template_name,
        additional_data=data)


def get_trigger_missed_jobs_job_config(args, config, build_file):
    template_name = 'release/release_trigger-jobs_job.xml.em'
    data = {'missed_jobs': True}
    return _get_job_config(
        args, config, build_file.notify_emails, template_name,
        additional_data=data)


def get_import_upstream_job_config(args, config, build_file, package_format):
    template_name = 'release/%s/import_upstream_job.xml.em' % package_format
    data = {
        'credential_id': build_file.upload_credential_id,
        'dest_credential_id': build_file.upload_destination_credential_id,
    }
    return _get_job_config(
        args, config, config.notify_emails, template_name,
        additional_data=data)


def _get_job_config(
    args, config, recipients, template_name, additional_data=None
):
    repository_args, script_generating_key_files = \
        get_repositories_and_script_generating_key_files(config=config)

    job_data = dict(additional_data) if additional_data is not None else {}
    job_data.update({
        'script_generating_key_files': script_generating_key_files,

        'config_url': args.config_url,
        'rosdistro_name': args.rosdistro_name,
        'release_build_name': args.release_build_name,
        'repository_args': repository_args,

        'ros_buildfarm_repository': get_repository(),

        'credentials_src': os.path.join(
            '~', os.path.dirname(get_relative_credential_path())),
        'credentials_dst': os.path.join(
            '/home/buildfarm',
            os.path.dirname(get_relative_credential_path())),

        'recipients': recipients,
    })
    job_config = expand_template(template_name, job_data)
    return job_config


def _get_trigger_broken_with_non_broken_upstream_job_config(
        rosdistro_name, release_build_name, build_file):
    template_name = \
        'release/release_trigger-broken-with-non-broken-upstream_job.xml.em'
    job_data = {
        'source_project_name_prefix': get_release_source_view_prefix(
            rosdistro_name),
        'binary_project_name_prefix': get_release_binary_view_prefix(
            rosdistro_name, release_build_name),

        'recipients': build_file.notify_emails,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


if __name__ == '__main__':
    main()
