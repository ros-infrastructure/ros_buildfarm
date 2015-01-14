#!/usr/bin/env python3

import argparse
import copy
import sys

from ros_buildfarm.argument import add_argument_config_url
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
    args = parser.parse_args(argv)

    config = get_index(args.config_url)
    job_config = get_job_config(args, config)

    jenkins = connect(config.jenkins_url)

    configure_management_view(jenkins)

    prefix = get_release_job_prefix(args.rosdistro_name)
    job_name = '%s_repos-status-page' % prefix
    configure_job(jenkins, job_name, job_config)


def get_job_config(args, config):
    template_name = 'status/repos_status_page_job.xml.em'

    targets_by_repo = get_targets_by_repo(config, args.rosdistro_name)
    status_pages = {}
    for name, repo_urls in config.status_page_repositories.items():
        data = get_status_page_data(repo_urls, targets_by_repo)
        if data is not None:
            status_pages[name] = data
        else:
            print(("Skipping repos status page '%s' since no repository URL" +
                   "matches any of the release build files") % name)

    job_data = copy.deepcopy(args.__dict__)
    job_data.update({
        'ros_buildfarm_repository': get_repository(),

        'status_pages': status_pages,

        'notification_emails': config.notify_emails,
    })
    job_config = expand_template(template_name, job_data)
    return job_config


def get_targets_by_repo(config, ros_distro_name):
    # collect all target repositories (building) and their targets
    # from all release build files
    targets_by_repo = {}
    release_build_files = get_release_build_files(config, ros_distro_name)
    for release_build_name, release_build_file in release_build_files.items():
        target_repository = release_build_file.target_repository
        if target_repository not in targets_by_repo:
            targets_by_repo[target_repository] = []
        # TODO support other OS names
        if 'ubuntu' in release_build_file.targets:
            targets = release_build_file.targets['ubuntu']
            for os_code_name in sorted(targets.keys()):
                target = '%s:source' % os_code_name
                if target not in targets_by_repo[target_repository]:
                    targets_by_repo[target_repository].append(target)
                for arch in sorted(targets[os_code_name].keys()):
                    target = '%s:%s' % (os_code_name, arch)
                    if target not in targets_by_repo[target_repository]:
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
    data['os_code_name_and_arch_tuples'] = targets
    return data


if __name__ == '__main__':
    main()
