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

from __future__ import print_function

from collections import OrderedDict
import sys

from catkin_pkg.package import parse_package_string
from ros_buildfarm.common import get_default_node_label
from ros_buildfarm.common import get_devel_job_name
from ros_buildfarm.common import get_devel_view_name
from ros_buildfarm.common import get_github_project_url
from ros_buildfarm.common import get_node_label
from ros_buildfarm.common \
    import get_repositories_and_script_generating_key_files
from ros_buildfarm.common import get_xunit_publisher_types_and_patterns
from ros_buildfarm.common import git_github_orgunit
from ros_buildfarm.common import JobValidationError
from ros_buildfarm.common import write_groovy_script_and_configs
from ros_buildfarm.config import get_distribution_file
from ros_buildfarm.config import get_index as get_config_index
from ros_buildfarm.config import get_source_build_files
from ros_buildfarm.git import get_repository
from ros_buildfarm.templates import expand_template
from rosdistro import get_distribution_cache
from rosdistro import get_index


def configure_devel_jobs(
        config_url, rosdistro_name, source_build_name, groovy_script=None,
        dry_run=False, whitelist_repository_names=None):
    """
    Configure all Jenkins devel jobs.

    L{configure_release_job} will be invoked for source repository and target
    which matches the build file criteria.
    """
    config = get_config_index(config_url)
    build_files = get_source_build_files(config, rosdistro_name)
    build_file = build_files[source_build_name]

    index = get_index(config.rosdistro_index_url)

    dist_cache = None
    if build_file.notify_maintainers:
        dist_cache = get_distribution_cache(index, rosdistro_name)

    # get targets
    targets = []
    for os_name in build_file.targets.keys():
        for os_code_name in build_file.targets[os_name].keys():
            for arch in build_file.targets[os_name][os_code_name]:
                targets.append((os_name, os_code_name, arch))
    print('The build file contains the following targets:')
    for os_name, os_code_name, arch in targets:
        print('  -', os_name, os_code_name, arch)

    dist_file = get_distribution_file(index, rosdistro_name, build_file)
    if not dist_file:
        print('No distribution file matches the build file')
        return

    devel_view_name = get_devel_view_name(
        rosdistro_name, source_build_name, pull_request=False)
    pull_request_view_name = get_devel_view_name(
        rosdistro_name, source_build_name, pull_request=True)

    # all further configuration will be handled by either the Jenkins API
    # or by a generated groovy script
    from ros_buildfarm.jenkins import connect
    jenkins = connect(config.jenkins_url) if groovy_script is None else False

    view_configs = {}
    views = {}
    if build_file.test_commits_force is not False:
        views[devel_view_name] = configure_devel_view(
            jenkins, devel_view_name, dry_run=dry_run)
    if build_file.test_pull_requests_force is not False:
        views[pull_request_view_name] = configure_devel_view(
            jenkins, pull_request_view_name, dry_run=dry_run)
    if not jenkins:
        view_configs.update(views)
    groovy_data = {
        'dry_run': dry_run,
        'expected_num_views': len(view_configs),
    }

    repo_names = dist_file.repositories.keys()
    filtered_repo_names = build_file.filter_repositories(repo_names)

    devel_job_names = []
    pull_request_job_names = []
    job_configs = OrderedDict()
    for repo_name in sorted(repo_names):
        if whitelist_repository_names:
            if repo_name not in whitelist_repository_names:
                print(
                    "Skipping repository '%s' not in explicitly passed list" %
                    repo_name, file=sys.stderr)
                continue

        is_disabled = repo_name not in filtered_repo_names
        if is_disabled and build_file.skip_ignored_repositories:
            print("Skipping ignored repository '%s'" % repo_name,
                  file=sys.stderr)
            continue

        repo = dist_file.repositories[repo_name]
        if not repo.source_repository:
            print("Skipping repository '%s': no source section" % repo_name)
            continue
        if not repo.source_repository.version:
            print("Skipping repository '%s': no source version" % repo_name)
            continue

        job_types = []
        # check for testing commits
        if build_file.test_commits_force is False:
            print(("Skipping repository '%s': 'test_commits' is forced to " +
                   "false in the build file") % repo_name)
        elif repo.source_repository.test_commits is False:
            print(("Skipping repository '%s': 'test_commits' of the " +
                   "repository set to false") % repo_name)
        elif repo.source_repository.test_commits is None and \
                not build_file.test_commits_default:
            print(("Skipping repository '%s': 'test_commits' defaults to " +
                   "false in the build file") % repo_name)
        else:
            job_types.append('commit')

        if not is_disabled:
            # check for testing pull requests
            if build_file.test_pull_requests_force is False:
                # print(("Skipping repository '%s': 'test_pull_requests' " +
                #        "is forced to false in the build file") % repo_name)
                pass
            elif repo.source_repository.test_pull_requests is False:
                # print(("Skipping repository '%s': 'test_pull_requests' of " +
                #        "the repository set to false") % repo_name)
                pass
            elif repo.source_repository.test_pull_requests is None and \
                    not build_file.test_pull_requests_default:
                # print(("Skipping repository '%s': 'test_pull_requests' " +
                #        "defaults to false in the build file") % repo_name)
                pass
            else:
                print("Pull request job for repository '%s'" % repo_name)
                job_types.append('pull_request')

        # check for abi support
        run_abichecker = False
        if build_file.test_abi_force is False:
            pass
        elif getattr(repo.source_repository, 'test_abi', None) is False:
            pass
        elif getattr(repo.source_repository, 'test_abi', None) is None and \
                not build_file.test_abi_default:
            pass
        else:
            print("ABI checking enabled for repository '%s'" % repo_name)
            run_abichecker = True

        # check for gpu support
        require_gpu_support = False
        if getattr(repo.source_repository, 'tests_require_gpu', None) is False:
            pass
        elif getattr(repo.source_repository, 'tests_require_gpu', None) is None and \
                not build_file.tests_require_gpu_default:
            pass
        else:
            print("GPU support is required for repository '%s'" % repo_name)
            require_gpu_support = True

        for job_type in job_types:
            pull_request = job_type == 'pull_request'
            for os_name, os_code_name, arch in targets:
                try:
                    job_name, job_config = configure_devel_job(
                        config_url, rosdistro_name, source_build_name,
                        repo_name, os_name, os_code_name, arch, pull_request,
                        config=config, build_file=build_file,
                        index=index, dist_file=dist_file,
                        dist_cache=dist_cache, jenkins=jenkins, views=views,
                        is_disabled=is_disabled,
                        groovy_script=groovy_script,
                        dry_run=dry_run,
                        run_abichecker=run_abichecker,
                        require_gpu_support=require_gpu_support)
                    if not pull_request:
                        devel_job_names.append(job_name)
                    else:
                        pull_request_job_names.append(job_name)
                    if groovy_script is not None:
                        print("Configuration for job '%s'" % job_name)
                        job_configs[job_name] = job_config
                except JobValidationError as e:
                    print(e.message, file=sys.stderr)

    groovy_data['expected_num_jobs'] = len(job_configs)
    groovy_data['job_prefixes_and_names'] = {}

    devel_job_prefix = '%s__' % devel_view_name
    pull_request_job_prefix = '%s__' % pull_request_view_name
    if not whitelist_repository_names:
        groovy_data['job_prefixes_and_names']['devel'] = \
            (devel_job_prefix, devel_job_names)
        groovy_data['job_prefixes_and_names']['pull_request'] = \
            (pull_request_job_prefix, pull_request_job_names)

        if groovy_script is None:
            # delete obsolete jobs in these views
            from ros_buildfarm.jenkins import remove_jobs
            print('Removing obsolete devel jobs')
            remove_jobs(
                jenkins, devel_job_prefix, devel_job_names, dry_run=dry_run)
            print('Removing obsolete pull request jobs')
            remove_jobs(
                jenkins, pull_request_job_prefix, pull_request_job_names,
                dry_run=dry_run)
    if groovy_script is not None:
        print(
            "Writing groovy script '%s' to reconfigure %d views and %d jobs" %
            (groovy_script, len(view_configs), len(job_configs)))
        content = expand_template(
            'snippet/reconfigure_jobs.groovy.em', groovy_data)
        write_groovy_script_and_configs(
            groovy_script, content, job_configs, view_configs=view_configs)


def configure_devel_job(
        config_url, rosdistro_name, source_build_name,
        repo_name, os_name, os_code_name, arch,
        pull_request=False,
        config=None, build_file=None,
        index=None, dist_file=None, dist_cache=None,
        jenkins=None, views=None,
        is_disabled=False,
        groovy_script=None,
        source_repository=None,
        build_targets=None,
        dry_run=False,
        run_abichecker=None,
        require_gpu_support=None):
    """
    Configure a single Jenkins devel job.

    This includes the following steps:
    - clone the source repository to use
    - clone the ros_buildfarm repository
    - write the distribution repository keys into files
    - invoke the release/run_devel_job.py script
    """
    if config is None:
        config = get_config_index(config_url)
    if build_file is None:
        build_files = get_source_build_files(config, rosdistro_name)
        build_file = build_files[source_build_name]
    # Overwrite build_file.targets if build_targets is specified
    if build_targets is not None:
        build_file.targets = build_targets

    if index is None:
        index = get_index(config.rosdistro_index_url)
    if dist_file is None:
        dist_file = get_distribution_file(index, rosdistro_name, build_file)
        if not dist_file:
            raise JobValidationError(
                'No distribution file matches the build file')

    repo_names = dist_file.repositories.keys()

    if repo_name is not None:
        if repo_name not in repo_names:
            raise JobValidationError(
                "Invalid repository name '%s' " % repo_name +
                'choose one of the following: %s' %
                ', '.join(sorted(repo_names)))

        repo = dist_file.repositories[repo_name]
        if not repo.source_repository:
            raise JobValidationError(
                "Repository '%s' has no source section" % repo_name)
        if not repo.source_repository.version:
            raise JobValidationError(
                "Repository '%s' has no source version" % repo_name)
        source_repository = repo.source_repository

    if os_name not in build_file.targets.keys():
        raise JobValidationError(
            "Invalid OS name '%s' " % os_name +
            'choose one of the following: ' +
            ', '.join(sorted(build_file.targets.keys())))
    if os_code_name not in build_file.targets[os_name].keys():
        raise JobValidationError(
            "Invalid OS code name '%s' " % os_code_name +
            'choose one of the following: ' +
            ', '.join(sorted(build_file.targets[os_name].keys())))
    if arch not in build_file.targets[os_name][os_code_name]:
        raise JobValidationError(
            "Invalid architecture '%s' " % arch +
            'choose one of the following: %s' % ', '.join(sorted(
                build_file.targets[os_name][os_code_name])))

    if dist_cache is None and build_file.notify_maintainers:
        dist_cache = get_distribution_cache(index, rosdistro_name)
    if jenkins is None:
        from ros_buildfarm.jenkins import connect
        jenkins = connect(config.jenkins_url)
    if views is None:
        view_name = get_devel_view_name(
            rosdistro_name, source_build_name, pull_request=pull_request)
        configure_devel_view(jenkins, view_name, dry_run=dry_run)

    job_name = get_devel_job_name(
        rosdistro_name, source_build_name,
        repo_name, os_name, os_code_name, arch, pull_request)

    job_config = _get_devel_job_config(
        index, config, rosdistro_name, source_build_name,
        build_file, os_name, os_code_name, arch, source_repository,
        repo_name, pull_request, job_name, dist_cache=dist_cache,
        is_disabled=is_disabled, run_abichecker=run_abichecker,
        require_gpu_support=require_gpu_support)
    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        from ros_buildfarm.jenkins import configure_job
        configure_job(jenkins, job_name, job_config, dry_run=dry_run)

    return job_name, job_config


def configure_devel_view(jenkins, view_name, dry_run=False):
    from ros_buildfarm.jenkins import configure_view
    return configure_view(
        jenkins, view_name, include_regex='%s__.+' % view_name,
        template_name='dashboard_view_devel_jobs.xml.em', dry_run=dry_run)


def _get_devel_job_config(
        index, config, rosdistro_name, source_build_name,
        build_file, os_name, os_code_name, arch, source_repo_spec,
        repo_name, pull_request, job_name, dist_cache=None,
        is_disabled=False, run_abichecker=None,
        require_gpu_support=None):
    template_name = 'devel/devel_job.xml.em'

    repository_args, script_generating_key_files = \
        get_repositories_and_script_generating_key_files(build_file=build_file)

    build_environment_variables = []
    if build_file.build_environment_variables:
        build_environment_variables = [
            '%s=%s' % (var, value)
            for var, value in sorted(build_file.build_environment_variables.items())]

    maintainer_emails = set([])
    if build_file.notify_maintainers and dist_cache and repo_name and \
            repo_name in dist_cache.distribution_file.repositories:
        # add maintainers listed in latest release to recipients
        repo = dist_cache.distribution_file.repositories[repo_name]
        if repo.release_repository:
            for pkg_name in repo.release_repository.package_names:
                if pkg_name not in dist_cache.release_package_xmls:
                    continue
                pkg_xml = dist_cache.release_package_xmls[pkg_name]
                pkg = parse_package_string(pkg_xml)
                for m in pkg.maintainers:
                    maintainer_emails.add(m.email)

    job_priority = \
        build_file.jenkins_commit_job_priority \
        if not pull_request \
        else build_file.jenkins_pull_request_job_priority

    distribution_type = index.distributions[rosdistro_name] \
        .get('distribution_type', 'ros1')
    assert distribution_type in ('ros1', 'ros2')
    ros_version = 1 if distribution_type == 'ros1' else 2

    job_data = {
        'github_url': get_github_project_url(source_repo_spec.url),

        'job_priority': job_priority,
        'node_label': get_node_label(
            build_file.jenkins_job_label,
            get_default_node_label('%s_%s_%s' % (
                rosdistro_name, 'devel', source_build_name))),

        'pull_request': pull_request,

        'source_repo_spec': source_repo_spec,

        'disabled': is_disabled,

        # this should not be necessary
        'job_name': job_name,

        'github_orgunit': git_github_orgunit(source_repo_spec.url),

        'ros_buildfarm_repository': get_repository(),

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_index_url': config.rosdistro_index_url,
        'rosdistro_name': rosdistro_name,
        'source_build_name': source_build_name,
        'os_name': os_name,
        'os_code_name': os_code_name,
        'arch': arch,
        'repository_args': repository_args,
        'build_tool': build_file.build_tool,
        'build_tool_args': build_file.build_tool_args,
        'build_tool_test_args': build_file.build_tool_test_args,
        'ros_version': ros_version,
        'build_environment_variables': build_environment_variables,

        'run_abichecker': run_abichecker,
        'require_gpu_support': require_gpu_support,
        'notify_compiler_warnings': build_file.notify_compiler_warnings,
        'notify_emails': build_file.notify_emails,
        'maintainer_emails': maintainer_emails,
        'notify_maintainers': build_file.notify_maintainers,
        'notify_committers': build_file.notify_committers,
        'notify_pull_requests': build_file.notify_pull_requests,

        'timeout_minutes': build_file.jenkins_job_timeout,

        # only Ubuntu Focal has a new enough pytest version which generates
        # JUnit compliant result files
        'xunit_publisher_types': get_xunit_publisher_types_and_patterns(
            ros_version, os_name == 'ubuntu' and os_code_name != 'bionic'),

        'git_ssh_credential_id': config.git_ssh_credential_id,

        'collate_test_stats': build_file.collate_test_stats,

        'benchmark_patterns': build_file.benchmark_patterns,
        'benchmark_schema': build_file.benchmark_schema,

        'shared_ccache': build_file.shared_ccache,
    }
    job_config = expand_template(template_name, job_data)
    return job_config
