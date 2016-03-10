#!/usr/bin/env python3

import argparse
import copy
import sys

from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_dry_run
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import \
    get_repositories_and_script_generating_key_files
from ros_buildfarm.config import get_index
from ros_buildfarm.config import get_release_build_files
from ros_buildfarm.common import get_release_job_prefix
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

    job_data = copy.deepcopy(args.__dict__)
    job_data.update({
        'ros_buildfarm_repository': get_repository(),

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_index_url': config.rosdistro_index_url,

        'repository_args': repository_args,

        'reconfigure_job_names': reconfigure_job_names,

        'notification_emails':
        config.distributions[args.rosdistro_name]['notification_emails'],

        'git_ssh_credential_id': config.git_ssh_credential_id,
    })
    job_config = expand_template(template_name, job_data)
    return job_config


if __name__ == '__main__':
    main()
