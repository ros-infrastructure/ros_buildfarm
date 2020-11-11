# Copyright 2019 Open Source Robotics Foundation, Inc.
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

from ros_buildfarm.common import get_ci_job_name
from ros_buildfarm.common import get_ci_view_name
from ros_buildfarm.common import get_default_node_label
from ros_buildfarm.common import get_node_label
from ros_buildfarm.common \
    import get_repositories_and_script_generating_key_files
from ros_buildfarm.common import get_xunit_publisher_types_and_patterns
from ros_buildfarm.common import JobValidationError
from ros_buildfarm.common import write_groovy_script_and_configs
from ros_buildfarm.config import get_ci_build_files
from ros_buildfarm.config import get_distribution_file
from ros_buildfarm.config import get_index as get_config_index
from ros_buildfarm.git import get_repository
from ros_buildfarm.templates import expand_template
from rosdistro import get_index


def configure_ci_jobs(
        config_url, rosdistro_name, ci_build_names=None,
        groovy_script=None, dry_run=False):
    """Configure all Jenkins CI jobs."""
    config = get_config_index(config_url)
    build_files = get_ci_build_files(config, rosdistro_name)

    if not ci_build_names:
        ci_build_names = build_files.keys()

    for ci_build_name in ci_build_names:
        _configure_ci_jobs(
            config, build_files, config_url, rosdistro_name, ci_build_name,
            groovy_script=groovy_script, dry_run=dry_run)


def _configure_ci_jobs(
        config, build_files, config_url, rosdistro_name, ci_build_name,
        groovy_script=None, dry_run=False):
    """Configure all Jenkins CI jobs for a specific CI build name."""
    build_file = build_files[ci_build_name]

    index = get_index(config.rosdistro_index_url)

    # get targets
    targets = []
    for os_name in build_file.targets.keys():
        for os_code_name in build_file.targets[os_name].keys():
            for arch in build_file.targets[os_name][os_code_name]:
                targets.append((os_name, os_code_name, arch))
    print(
        "The build file '%s' contains the following targets:" % ci_build_name)
    for os_name, os_code_name, arch in targets:
        print('  -', os_name, os_code_name, arch)

    dist_file = get_distribution_file(index, rosdistro_name, build_file)
    if not dist_file:
        print('No distribution file matches the build file')
        return

    ci_view_name = get_ci_view_name(rosdistro_name)

    # all further configuration will be handled by either the Jenkins API
    # or by a generated groovy script
    from ros_buildfarm.jenkins import connect
    jenkins = connect(config.jenkins_url) if groovy_script is None else False

    view_configs = {}
    views = {
        ci_view_name: configure_ci_view(
            jenkins, ci_view_name, dry_run=dry_run)
    }
    if not jenkins:
        view_configs.update(views)
    groovy_data = {
        'dry_run': dry_run,
        'expected_num_views': len(view_configs),
    }

    ci_job_names = []
    job_configs = OrderedDict()

    is_disabled = False

    for os_name, os_code_name, arch in targets:
        try:
            job_name, job_config = configure_ci_job(
                config_url, rosdistro_name, ci_build_name,
                os_name, os_code_name, arch,
                config=config, build_file=build_file,
                index=index, dist_file=dist_file,
                jenkins=jenkins, views=views,
                is_disabled=is_disabled,
                groovy_script=groovy_script,
                dry_run=dry_run,
                trigger_timer=build_file.jenkins_job_schedule)
            ci_job_names.append(job_name)
            if groovy_script is not None:
                print("Configuration for job '%s'" % job_name)
                job_configs[job_name] = job_config
        except JobValidationError as e:
            print(e.message, file=sys.stderr)

    groovy_data['expected_num_jobs'] = len(job_configs)
    groovy_data['job_prefixes_and_names'] = {}

    if groovy_script is not None:
        print(
            "Writing groovy script '%s' to reconfigure %d jobs" %
            (groovy_script, len(job_configs)))
        content = expand_template(
            'snippet/reconfigure_jobs.groovy.em', groovy_data)
        write_groovy_script_and_configs(
            groovy_script, content, job_configs, view_configs)


def configure_ci_job(
        config_url, rosdistro_name, ci_build_name,
        os_name, os_code_name, arch,
        config=None, build_file=None,
        index=None, dist_file=None,
        jenkins=None, views=None,
        is_disabled=False,
        groovy_script=None,
        build_targets=None,
        dry_run=False,
        underlay_source_paths=None,
        trigger_timer=None):
    """
    Configure a single Jenkins CI job.

    This includes the following steps:
    - clone the ros_buildfarm repository
    - write the distribution repository keys into files
    - invoke the ci/run_ci_job.py script
    """
    if config is None:
        config = get_config_index(config_url)
    if build_file is None:
        build_files = get_ci_build_files(config, rosdistro_name)
        build_file = build_files[ci_build_name]
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

    underlay_source_jobs = [
        get_ci_job_name(
            rosdistro_name, os_name, os_code_name, arch, underlay_job)
        for underlay_job in build_file.underlay_from_ci_jobs]
    underlay_source_paths = (underlay_source_paths or []) + \
        ['$UNDERLAY%d_JOB_SPACE' % (index + 1) for index in range(len(underlay_source_jobs))]

    trigger_jobs = [
        get_ci_job_name(
            rosdistro_name, os_name, os_code_name, arch, trigger_job)
        for trigger_job in build_file.jenkins_job_upstream_triggers]

    if jenkins is None:
        from ros_buildfarm.jenkins import connect
        jenkins = connect(config.jenkins_url)
    if views is None:
        view_name = get_ci_view_name(rosdistro_name)
        configure_ci_view(jenkins, view_name, dry_run=dry_run)

    job_name = get_ci_job_name(
        rosdistro_name, os_name, os_code_name, arch, ci_build_name)

    job_config = _get_ci_job_config(
        index, rosdistro_name, build_file, os_name,
        os_code_name, arch,
        build_file.repos_files,
        build_file.repository_names,
        underlay_source_jobs,
        underlay_source_paths,
        trigger_timer, trigger_jobs,
        is_disabled=is_disabled)
    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        from ros_buildfarm.jenkins import configure_job
        configure_job(jenkins, job_name, job_config, dry_run=dry_run)

    return job_name, job_config


def configure_ci_view(jenkins, view_name, dry_run=False):
    from ros_buildfarm.jenkins import configure_view
    return configure_view(
        jenkins, view_name, include_regex='%s__.+' % view_name,
        template_name='dashboard_view_devel_jobs.xml.em', dry_run=dry_run)


def _get_ci_job_config(
        index, rosdistro_name, build_file, os_name,
        os_code_name, arch,
        repos_files, repository_names, underlay_source_jobs,
        underlay_source_paths, trigger_timer,
        trigger_jobs, is_disabled=False):
    template_name = 'ci/ci_job.xml.em'

    repository_args, script_generating_key_files = \
        get_repositories_and_script_generating_key_files(build_file=build_file)

    build_environment_variables = []
    if build_file.build_environment_variables:
        build_environment_variables = [
            '%s=%s' % (var, value)
            for var, value in sorted(build_file.build_environment_variables.items())]

    distribution_type = index.distributions[rosdistro_name] \
        .get('distribution_type', 'ros1')
    assert distribution_type in ('ros1', 'ros2')
    ros_version = 1 if distribution_type == 'ros1' else 2

    for index in range(len(underlay_source_jobs)):
        assert '$UNDERLAY%d_JOB_SPACE' % (index + 1) in underlay_source_paths

    job_data = {
        'job_priority': build_file.jenkins_job_priority,
        'job_weight': build_file.jenkins_job_weight,
        'node_label': get_node_label(
            build_file.jenkins_job_label,
            get_default_node_label('%s_%s' % (
                rosdistro_name, 'ci'))),

        'disabled': is_disabled,

        'ros_buildfarm_repository': get_repository(),

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_name': rosdistro_name,
        'os_name': os_name,
        'os_code_name': os_code_name,
        'arch': arch,
        'repository_args': repository_args,
        'build_tool': build_file.build_tool,
        'ros_version': ros_version,
        'build_environment_variables': build_environment_variables,

        'timeout_minutes': build_file.jenkins_job_timeout,

        'repos_file_urls': repos_files,
        'repository_names': repository_names,

        'skip_rosdep_keys': build_file.skip_rosdep_keys,
        'install_packages': build_file.install_packages,
        'package_selection_args': build_file.package_selection_args,
        'build_tool_args': build_file.build_tool_args,
        'build_tool_test_args': build_file.build_tool_test_args,
        'test_branch': build_file.test_branch,

        'underlay_source_jobs': underlay_source_jobs,
        'underlay_source_paths': underlay_source_paths,
        'trigger_timer': trigger_timer,
        'trigger_jobs': trigger_jobs,

        'archive_files': build_file.archive_files,

        'show_images': build_file.show_images,
        'show_plots': build_file.show_plots,

        # Allow per-job authorization for CI builds.
        'project_authorization_xml': build_file.project_authorization_xml,

        # only Ubuntu Focal has a new enough pytest version which generates
        # JUnit compliant result files
        'xunit_publisher_types': get_xunit_publisher_types_and_patterns(
            ros_version, os_name == 'ubuntu' and os_code_name != 'bionic'),

        'benchmark_patterns': build_file.benchmark_patterns,
        'benchmark_schema': build_file.benchmark_schema,

        'shared_ccache': build_file.shared_ccache,
    }
    job_config = expand_template(template_name, job_data)
    return job_config
