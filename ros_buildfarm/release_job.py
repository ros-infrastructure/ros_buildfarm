# Copyright 2014-2020 Open Source Robotics Foundation, Inc.
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

from ros_buildfarm.common import filter_blocked_dependent_package_names
from ros_buildfarm.common import filter_buildfile_packages_recursively
from ros_buildfarm.common import get_binarydeb_job_name
from ros_buildfarm.common import get_default_node_label
from ros_buildfarm.common import get_direct_dependencies
from ros_buildfarm.common import get_github_project_url
from ros_buildfarm.common import get_implicitly_ignored_package_names
from ros_buildfarm.common import get_node_label
from ros_buildfarm.common import get_os_package_name
from ros_buildfarm.common import get_package_condition_context
from ros_buildfarm.common import get_package_manifests
from ros_buildfarm.common import get_release_binary_view_name
from ros_buildfarm.common import get_release_job_prefix
from ros_buildfarm.common import get_release_source_view_name
from ros_buildfarm.common import get_release_view_name
from ros_buildfarm.common \
    import get_repositories_and_script_generating_key_files
from ros_buildfarm.common import get_sourcedeb_job_name
from ros_buildfarm.common import get_system_architecture
from ros_buildfarm.common import JobValidationError
from ros_buildfarm.common import package_format_mapping
from ros_buildfarm.common import write_groovy_script_and_configs
from ros_buildfarm.config import get_distribution_file
from ros_buildfarm.config import get_index as get_config_index
from ros_buildfarm.config import get_release_build_files
from ros_buildfarm.git import get_repository
from ros_buildfarm.package_repo import get_package_repo_data
from ros_buildfarm.templates import expand_template
from rosdistro import get_cached_distribution
from rosdistro import get_distribution_cache
from rosdistro import get_distribution_file as rosdistro_get_distribution_file
from rosdistro import get_index


def configure_release_jobs(
        config_url, rosdistro_name, release_build_name, groovy_script=None,
        dry_run=False, whitelist_package_names=None):
    """
    Configure all Jenkins release jobs.

    L{configure_release_job} will be invoked for every released package and
    target which matches the build file criteria.

    Additionally a job to import Debian packages into the Debian repository is
    created.
    """
    config = get_config_index(config_url)
    build_files = get_release_build_files(config, rosdistro_name)
    build_file = build_files[release_build_name]

    index = get_index(config.rosdistro_index_url)

    # get targets
    platforms = []
    for os_name in build_file.targets.keys():
        for os_code_name in build_file.targets[os_name].keys():
            platforms.append((os_name, os_code_name))
    print('The build file contains the following targets:')
    for os_name, os_code_name in platforms:
        print('  - %s %s: %s' % (os_name, os_code_name, ', '.join(
            build_file.targets[os_name][os_code_name])))

    dist_file = get_distribution_file(index, rosdistro_name, build_file)
    if not dist_file:
        print('No distribution file matches the build file')
        return

    pkg_names = dist_file.release_packages.keys()
    cached_pkgs = _get_and_parse_distribution_cache(index, rosdistro_name, pkg_names)
    filtered_pkg_names = build_file.filter_packages(pkg_names)
    explicitly_ignored_without_recursion_pkg_names = \
        set(pkg_names) & set(build_file.package_ignore_list)
    explicitly_ignored_pkg_names = \
        set(pkg_names) - set(filtered_pkg_names) - explicitly_ignored_without_recursion_pkg_names
    if explicitly_ignored_pkg_names:
        print(('The following packages are being %s because of ' +
               'white-/blacklisting:') %
              ('ignored' if build_file.skip_ignored_packages else 'disabled'))
        for pkg_name in sorted(explicitly_ignored_pkg_names):
            print('  -', pkg_name)

        implicitly_ignored_pkg_names = get_implicitly_ignored_package_names(
            cached_pkgs, explicitly_ignored_pkg_names)
        if implicitly_ignored_pkg_names:
            print(('The following packages are being %s because their ' +
                   'dependencies are being ignored:') % ('ignored'
                  if build_file.skip_ignored_packages else 'disabled'))
            for pkg_name in sorted(implicitly_ignored_pkg_names):
                print('  -', pkg_name)
            filtered_pkg_names = \
                set(filtered_pkg_names) - implicitly_ignored_pkg_names

    if explicitly_ignored_without_recursion_pkg_names:
        print(('The following packages are being %s because of ' +
               'ignore-listing:') %
              ('ignored' if build_file.skip_ignored_packages else 'disabled'))
        for pkg_name in sorted(explicitly_ignored_without_recursion_pkg_names):
            print('  -', pkg_name)
        filtered_pkg_names.difference_update(explicitly_ignored_without_recursion_pkg_names)

    # all further configuration will be handled by either the Jenkins API
    # or by a generated groovy script
    jenkins = False
    if groovy_script is None:
        from ros_buildfarm.jenkins import connect
        jenkins = connect(config.jenkins_url)

    all_view_configs = {}
    all_job_configs = OrderedDict()

    job_name, job_config = configure_import_package_job(
        config_url, rosdistro_name, release_build_name,
        config=config, build_file=build_file, jenkins=jenkins, dry_run=dry_run)
    if not jenkins:
        all_job_configs[job_name] = job_config

    job_name, job_config = configure_sync_packages_to_main_job(
        config_url, rosdistro_name, release_build_name,
        config=config, build_file=build_file, jenkins=jenkins, dry_run=dry_run)
    if not jenkins:
        all_job_configs[job_name] = job_config

    for os_name, os_code_name in platforms:
        for arch in sorted(build_file.targets[os_name][os_code_name]):
            job_name, job_config = configure_sync_packages_to_testing_job(
                config_url, rosdistro_name, release_build_name,
                os_name, os_code_name, arch,
                config=config, build_file=build_file, jenkins=jenkins,
                dry_run=dry_run)
            if not jenkins:
                all_job_configs[job_name] = job_config

    targets = []
    for os_name, os_code_name in platforms:
        targets.append((os_name, os_code_name, 'source'))
        for arch in build_file.targets[os_name][os_code_name]:
            targets.append((os_name, os_code_name, arch))
    views = configure_release_views(
        jenkins, rosdistro_name, release_build_name, targets,
        dry_run=dry_run)
    if not jenkins:
        all_view_configs.update(views)
    groovy_data = {
        'dry_run': dry_run,
        'expected_num_views': len(views),
    }

    # binary jobs must be generated in topological order
    from ros_buildfarm.common import topological_order_packages
    for pkg_name in set(pkg_names).difference(cached_pkgs.keys()):
        print("Skipping package '%s': no released package.xml in cache" %
              (pkg_name), file=sys.stderr)
    ordered_pkg_tuples = topological_order_packages(cached_pkgs)

    other_build_files = [v for k, v in build_files.items() if k != release_build_name]

    all_source_job_names = []
    all_binary_job_names = []
    for pkg_name in [p.name for _, p in ordered_pkg_tuples]:
        if whitelist_package_names:
            if pkg_name not in whitelist_package_names:
                print("Skipping package '%s' not in the explicitly passed list" %
                      pkg_name, file=sys.stderr)
                continue

        pkg = dist_file.release_packages[pkg_name]
        repo_name = pkg.repository_name
        repo = dist_file.repositories[repo_name]
        is_disabled = pkg_name not in filtered_pkg_names
        if is_disabled and build_file.skip_ignored_packages:
            print("Skipping ignored package '%s' in repository '%s'" %
                  (pkg_name, repo_name), file=sys.stderr)
            continue
        if not repo.release_repository:
            print(("Skipping package '%s' in repository '%s': no release " +
                   "section") % (pkg_name, repo_name), file=sys.stderr)
            continue
        if not repo.release_repository.version:
            print(("Skipping package '%s' in repository '%s': no release " +
                   "version") % (pkg_name, repo_name), file=sys.stderr)
            continue

        for os_name, os_code_name in platforms:
            other_build_files_same_platform = []
            for other_build_file in other_build_files:
                if os_name not in other_build_file.targets:
                    continue
                if os_code_name not in other_build_file.targets[os_name]:
                    continue
                other_build_files_same_platform.append(other_build_file)

            try:
                source_job_names, binary_job_names, job_configs = \
                    configure_release_job(
                        config_url, rosdistro_name, release_build_name,
                        pkg_name, os_name, os_code_name,
                        config=config, build_file=build_file,
                        index=index, dist_file=dist_file,
                        cached_pkgs=cached_pkgs,
                        jenkins=jenkins, views=views,
                        generate_import_package_job=False,
                        generate_sync_packages_jobs=False,
                        is_disabled=is_disabled,
                        other_build_files_same_platform=other_build_files_same_platform,
                        groovy_script=groovy_script,
                        dry_run=dry_run)
                all_source_job_names += source_job_names
                all_binary_job_names += binary_job_names
                if groovy_script is not None:
                    print('Configuration for jobs: ' +
                          ', '.join(source_job_names + binary_job_names))
                    for source_job_name in source_job_names:
                        all_job_configs[source_job_name] = job_configs[source_job_name]
                    for binary_job_name in binary_job_names:
                        all_job_configs[binary_job_name] = job_configs[binary_job_name]
            except JobValidationError as e:
                print(e.message, file=sys.stderr)

    groovy_data['expected_num_jobs'] = len(all_job_configs)
    groovy_data['job_prefixes_and_names'] = {}

    # with an explicit list of packages we don't delete obsolete jobs
    if not whitelist_package_names:
        # delete obsolete binary jobs
        for os_name, os_code_name in platforms:
            for arch in build_file.targets[os_name][os_code_name]:
                binary_view = get_release_binary_view_name(
                    rosdistro_name, release_build_name,
                    os_name, os_code_name, arch)
                binary_job_prefix = '%s__' % binary_view

                excluded_job_names = set([
                    j for j in all_binary_job_names
                    if j.startswith(binary_job_prefix)])
                if groovy_script is None:
                    print("Removing obsolete binary jobs with prefix '%s'" %
                          binary_job_prefix)
                    from ros_buildfarm.jenkins import remove_jobs
                    remove_jobs(
                        jenkins, binary_job_prefix, excluded_job_names,
                        dry_run=dry_run)
                else:
                    binary_key = 'binary_%s_%s_%s' % \
                        (os_name, os_code_name, arch)
                    groovy_data['job_prefixes_and_names'][binary_key] = \
                        (binary_job_prefix, excluded_job_names)

        # delete obsolete source jobs
        # requires knowledge about all other release build files
        for os_name, os_code_name in platforms:
            other_source_job_names = []
            # get source job names for all other release build files
            for other_release_build_name in [
                    k for k in build_files.keys() if k != release_build_name]:
                other_build_file = build_files[other_release_build_name]
                other_dist_file = get_distribution_file(
                    index, rosdistro_name, other_build_file)
                if not other_dist_file:
                    continue

                if os_name not in other_build_file.targets or \
                        os_code_name not in other_build_file.targets[os_name]:
                    continue

                if other_build_file.skip_ignored_packages:
                    filtered_pkg_names = other_build_file.filter_packages(
                        pkg_names)
                else:
                    filtered_pkg_names = pkg_names
                for pkg_name in sorted(filtered_pkg_names):
                    pkg = other_dist_file.release_packages[pkg_name]
                    repo_name = pkg.repository_name
                    repo = other_dist_file.repositories[repo_name]
                    if not repo.release_repository:
                        continue
                    if not repo.release_repository.version:
                        continue

                    other_job_name = get_sourcedeb_job_name(
                        rosdistro_name, other_release_build_name,
                        pkg_name, os_name, os_code_name)
                    other_source_job_names.append(other_job_name)

            source_view_prefix = get_release_source_view_name(
                rosdistro_name, os_name, os_code_name)
            source_job_prefix = '%s__' % source_view_prefix
            excluded_job_names = set([
                j for j in (all_source_job_names + other_source_job_names)
                if j.startswith(source_job_prefix)])
            if groovy_script is None:
                print("Removing obsolete source jobs with prefix '%s'" %
                      source_job_prefix)
                from ros_buildfarm.jenkins import remove_jobs
                remove_jobs(
                    jenkins, source_job_prefix, excluded_job_names,
                    dry_run=dry_run)
            else:
                source_key = 'source_%s_%s' % (os_name, os_code_name)
                groovy_data['job_prefixes_and_names'][source_key] = (
                    source_job_prefix, excluded_job_names)

    if groovy_script is not None:
        print(
            "Writing groovy script '%s' to reconfigure %d views and %d jobs" %
            (groovy_script, len(all_view_configs), len(all_job_configs)))
        content = expand_template(
            'snippet/reconfigure_jobs.groovy.em', groovy_data)
        write_groovy_script_and_configs(
            groovy_script, content, all_job_configs,
            view_configs=all_view_configs)


def _get_and_parse_distribution_cache(index, rosdistro_name, pkg_names):
    from catkin_pkg.package import parse_package_string
    from catkin_pkg.package import Dependency
    dist_cache = get_distribution_cache(index, rosdistro_name)
    pkg_names = set(['ros_workspace']).union(pkg_names)
    cached_pkgs = {
        pkg_name: parse_package_string(pkg_xml)
        for pkg_name, pkg_xml in dist_cache.release_package_xmls.items()
        if pkg_name in pkg_names
    }

    condition_context = get_package_condition_context(index, rosdistro_name)
    for pkg in cached_pkgs.values():
        pkg.evaluate_conditions(condition_context)
    for pkg in cached_pkgs.values():
        for group_depend in pkg.group_depends:
            if group_depend.evaluated_condition is not False:
                group_depend.extract_group_members(cached_pkgs.values())

    # for ROS 2 distributions bloom injects a dependency on ros_workspace
    # into almost all packages (except its dependencies)
    # therefore the same dependency needs to to be injected here
    distribution_type = index.distributions[rosdistro_name].get(
        'distribution_type')
    if distribution_type == 'ros2' and 'ros_workspace' in cached_pkgs:
        no_ros_workspace_dep = set(['ros_workspace']).union(
            get_direct_dependencies('ros_workspace', cached_pkgs, pkg_names))

        for pkg_name, pkg in cached_pkgs.items():
            if pkg_name not in no_ros_workspace_dep:
                pkg.exec_depends.append(Dependency('ros_workspace'))

    return cached_pkgs


# Configure a Jenkins release job which consists of
# - a source deb job
# - N binary debs, one for each archicture
def configure_release_job(
        config_url, rosdistro_name, release_build_name,
        pkg_name, os_name, os_code_name,
        config=None, build_file=None,
        index=None, dist_file=None, cached_pkgs=None,
        jenkins=None, views=None,
        generate_import_package_job=True,
        generate_sync_packages_jobs=True,
        is_disabled=False, other_build_files_same_platform=None,
        groovy_script=None,
        filter_arches=None,
        dry_run=False):
    """
    Configure a Jenkins release job.

    The following jobs are created for each package:
    - M source jobs, one for each OS node name
    - M * N binary jobs, one for each combination of OS code name and arch
    """
    if config is None:
        config = get_config_index(config_url)
    if build_file is None:
        build_files = get_release_build_files(config, rosdistro_name)
        build_file = build_files[release_build_name]

    if index is None:
        index = get_index(config.rosdistro_index_url)
    if dist_file is None:
        dist_file = get_distribution_file(index, rosdistro_name, build_file)
        if not dist_file:
            raise JobValidationError(
                'No distribution file matches the build file')

    pkg_names = dist_file.release_packages.keys()

    if pkg_name not in pkg_names:
        raise JobValidationError(
            "Invalid package name '%s' " % pkg_name +
            'choose one of the following: ' + ', '.join(sorted(pkg_names)))

    pkg = dist_file.release_packages[pkg_name]
    repo_name = pkg.repository_name
    repo = dist_file.repositories[repo_name]

    if not repo.release_repository:
        raise JobValidationError(
            "Repository '%s' has no release section" % repo_name)

    if not repo.release_repository.version:
        raise JobValidationError(
            "Repository '%s' has no release version" % repo_name)

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

    if cached_pkgs is None and \
            (build_file.notify_maintainers or
             build_file.abi_incompatibility_assumed):
        cached_pkgs = _get_and_parse_distribution_cache(index, rosdistro_name, [pkg_name])
    if jenkins is None:
        from ros_buildfarm.jenkins import connect
        jenkins = connect(config.jenkins_url)
    if views is None:
        targets = []
        targets.append((os_name, os_code_name, 'source'))
        for arch in build_file.targets[os_name][os_code_name]:
            targets.append((os_name, os_code_name, arch))
        configure_release_views(
            jenkins, rosdistro_name, release_build_name, targets,
            dry_run=dry_run)

    if generate_import_package_job:
        configure_import_package_job(
            config_url, rosdistro_name, release_build_name,
            config=config, build_file=build_file, jenkins=jenkins,
            dry_run=dry_run)

    if generate_sync_packages_jobs:
        configure_sync_packages_to_main_job(
            config_url, rosdistro_name, release_build_name,
            config=config, build_file=build_file, jenkins=jenkins,
            dry_run=dry_run)
        for arch in build_file.targets[os_name][os_code_name]:
            configure_sync_packages_to_testing_job(
                config_url, rosdistro_name, release_build_name,
                os_name, os_code_name, arch,
                config=config, build_file=build_file, jenkins=jenkins,
                dry_run=dry_run)

    source_job_names = []
    binary_job_names = []
    job_configs = {}

    # sourcedeb job
    # since sourcedeb jobs are potentially being shared across multiple build
    # files the configuration has to take all of them into account in order to
    # generate a job which all build files agree on
    source_job_name = get_sourcedeb_job_name(
        rosdistro_name, release_build_name,
        pkg_name, os_name, os_code_name)

    # while the package is disabled in the current build file
    # it might be used by sibling build files
    is_source_disabled = is_disabled
    if is_source_disabled and other_build_files_same_platform:
        # check if sourcedeb job is used by any other build file with the same platform
        for other_build_file in other_build_files_same_platform:
            if other_build_file.filter_packages([pkg_name]):
                is_source_disabled = False
                break

    job_config = _get_sourcedeb_job_config(
        config_url, rosdistro_name, release_build_name,
        config, build_file, os_name, os_code_name,
        pkg_name, repo_name, repo.release_repository, cached_pkgs=cached_pkgs,
        is_disabled=is_source_disabled,
        other_build_files_same_platform=other_build_files_same_platform)
    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        from ros_buildfarm.jenkins import configure_job
        configure_job(jenkins, source_job_name, job_config, dry_run=dry_run)
    source_job_names.append(source_job_name)
    job_configs[source_job_name] = job_config

    dependency_names = []
    if build_file.abi_incompatibility_assumed:
        dependency_names = get_direct_dependencies(
            pkg_name, cached_pkgs, pkg_names)
        # if dependencies are not yet available in rosdistro cache
        # skip binary jobs
        if dependency_names is None:
            print(("Skipping binary jobs for package '%s' because it is not " +
                   "yet in the rosdistro cache") % pkg_name, file=sys.stderr)
            return source_job_names, binary_job_names, job_configs
        dependency_names.difference_update(build_file.package_ignore_list)

    # binarydeb jobs
    for arch in build_file.targets[os_name][os_code_name]:
        if filter_arches and arch not in filter_arches:
            continue

        job_name = get_binarydeb_job_name(
            rosdistro_name, release_build_name,
            pkg_name, os_name, os_code_name, arch)

        upstream_job_names = [source_job_name] + [
            get_binarydeb_job_name(
                rosdistro_name, release_build_name,
                dependency_name, os_name, os_code_name, arch)
            for dependency_name in dependency_names]

        job_config = _get_binarydeb_job_config(
            config_url, rosdistro_name, release_build_name,
            config, build_file, os_name, os_code_name, arch,
            pkg_name, repo_name, repo.release_repository,
            cached_pkgs=cached_pkgs, upstream_job_names=upstream_job_names,
            is_disabled=is_disabled)
        # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
        if isinstance(jenkins, object) and jenkins is not False:
            configure_job(jenkins, job_name, job_config, dry_run=dry_run)
        binary_job_names.append(job_name)
        job_configs[job_name] = job_config

    return source_job_names, binary_job_names, job_configs


def configure_release_views(
        jenkins, rosdistro_name, release_build_name, targets, dry_run=False):
    from ros_buildfarm.jenkins import configure_view
    views = {}

    for os_name, os_code_name, arch in targets:
        view_name = get_release_view_name(
            rosdistro_name, release_build_name, os_name, os_code_name,
            arch)
        if arch == 'source':
            include_regex = '%s__.+__%s_%s__source' % \
                (view_name, os_name, os_code_name)
        else:
            include_regex = '%s__.+__%s_%s_%s__binary' % \
                (view_name, os_name, os_code_name, arch)
        views[view_name] = configure_view(
            jenkins, view_name, include_regex=include_regex,
            template_name='dashboard_view_all_jobs.xml.em', dry_run=dry_run)

    return views


def _get_sourcedeb_job_config(
        config_url, rosdistro_name, release_build_name,
        config, build_file, os_name, os_code_name,
        pkg_name, repo_name, release_repository, cached_pkgs=None,
        is_disabled=False, other_build_files_same_platform=None):
    package_format = package_format_mapping[os_name]
    template_name = 'release/%s/sourcepkg_job.xml.em' % package_format

    repository_args, script_generating_key_files = \
        get_repositories_and_script_generating_key_files(build_file=build_file)

    sourcedeb_files = [
        'sourcedeb/*.debian.tar.gz',
        'sourcedeb/*.debian.tar.xz',
        'sourcedeb/*.dsc',
        'sourcedeb/*.orig.tar.gz',
        'sourcedeb/*_source.buildinfo',
        'sourcedeb/*_source.changes',
    ]

    # collect notify emails from all build files with the job enabled
    notify_emails = set(build_file.notify_emails)
    if other_build_files_same_platform:
        for other_build_file in other_build_files_same_platform:
            if other_build_file.filter_packages([pkg_name]):
                notify_emails.update(other_build_file.notify_emails)

    # notify maintainers if any build file (with the job enabled) requests it
    notify_maintainers = build_file.notify_maintainers
    if other_build_files_same_platform:
        for other_build_file in other_build_files_same_platform:
            if other_build_file.filter_packages([pkg_name]):
                if other_build_file.notify_maintainers:
                    notify_maintainers = True

    maintainer_emails = _get_maintainer_emails(cached_pkgs, pkg_name) \
        if notify_maintainers \
        else set([])

    job_data = {
        'github_url': get_github_project_url(release_repository.url),

        'job_priority': build_file.jenkins_source_job_priority,
        'node_label': get_node_label(
            build_file.jenkins_source_job_label,
            get_default_node_label('%s_%s%s' % (
                rosdistro_name, 'source', package_format))),

        'disabled': is_disabled,

        'ros_buildfarm_repository': get_repository(),

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_index_url': config.rosdistro_index_url,
        'rosdistro_name': rosdistro_name,
        'release_build_name': release_build_name,
        'pkg_name': pkg_name,
        'os_name': os_name,
        'os_code_name': os_code_name,
        'arch': get_system_architecture(),
        'repository_args': repository_args,

        'sourcedeb_files': sourcedeb_files,

        'import_package_job_name': get_import_package_job_name(
            rosdistro_name, package_format),
        'debian_package_name': get_os_package_name(
            rosdistro_name, pkg_name),

        'notify_emails': notify_emails,
        'maintainer_emails': maintainer_emails,
        'notify_maintainers': notify_maintainers,

        'timeout_minutes': build_file.jenkins_source_job_timeout,

        'credential_id': build_file.upload_credential_id,
        'dest_credential_id': build_file.upload_destination_credential_id,

        'git_ssh_credential_id': config.git_ssh_credential_id,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


def _get_binarydeb_job_config(
        config_url, rosdistro_name, release_build_name,
        config, build_file, os_name, os_code_name, arch,
        pkg_name, repo_name, release_repository,
        cached_pkgs=None, upstream_job_names=None,
        is_disabled=False):
    package_format = package_format_mapping[os_name]
    template_name = 'release/%s/binarypkg_job.xml.em' % package_format

    repository_args, script_generating_key_files = \
        get_repositories_and_script_generating_key_files(build_file=build_file)
    repository_args.append(
        '--target-repository ' + build_file.target_repository)

    binarydeb_files = [
        'binarydeb/*.changes',
        'binarydeb/*.deb',
        'binarydeb/*.ddeb',
    ]

    build_environment_variables = []
    if build_file.build_environment_variables:
        build_environment_variables = [
            '%s=%s' % (var, value)
            for var, value in sorted(build_file.build_environment_variables.items())]

    sync_to_testing_job_name = [get_sync_packages_to_testing_job_name(
        rosdistro_name, os_name, os_code_name, arch)]

    maintainer_emails = _get_maintainer_emails(cached_pkgs, pkg_name) \
        if build_file.notify_maintainers \
        else set([])

    job_data = {
        'github_url': get_github_project_url(release_repository.url),

        'job_priority': build_file.jenkins_binary_job_priority,
        'node_label': get_node_label(
            build_file.jenkins_binary_job_label,
            get_default_node_label('%s_%s%s_%s' % (
                rosdistro_name, 'binary', package_format, release_build_name))),

        'disabled': is_disabled,

        'upstream_projects': upstream_job_names,

        'ros_buildfarm_repository': get_repository(),

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_index_url': config.rosdistro_index_url,
        'rosdistro_name': rosdistro_name,
        'release_build_name': release_build_name,
        'pkg_name': pkg_name,
        'os_name': os_name,
        'os_code_name': os_code_name,
        'arch': arch,
        'repository_args': repository_args,

        'append_timestamp': build_file.abi_incompatibility_assumed,

        'binarydeb_files': binarydeb_files,
        'build_environment_variables': build_environment_variables,

        'import_package_job_name': get_import_package_job_name(
            rosdistro_name, package_format),
        'debian_package_name': get_os_package_name(
            rosdistro_name, pkg_name),

        'child_projects': sync_to_testing_job_name,

        'notify_emails': build_file.notify_emails,
        'maintainer_emails': maintainer_emails,
        'notify_maintainers': build_file.notify_maintainers,

        'timeout_minutes': build_file.jenkins_binary_job_timeout,

        'credential_id': build_file.upload_credential_id,
        'dest_credential_id': build_file.upload_destination_credential_id,

        'shared_ccache': build_file.shared_ccache,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


def configure_import_package_job(
        config_url, rosdistro_name, release_build_name,
        config=None, build_file=None, jenkins=None, dry_run=False):
    if config is None:
        config = get_config_index(config_url)
    if build_file is None:
        build_files = get_release_build_files(config, rosdistro_name)
        build_file = build_files[release_build_name]
    if jenkins is None:
        from ros_buildfarm.jenkins import connect
        jenkins = connect(config.jenkins_url)

    package_formats = set(
        package_format_mapping[os_name] for os_name in build_file.targets.keys())
    assert len(package_formats) == 1
    package_format = package_formats.pop()

    job_name = get_import_package_job_name(rosdistro_name, package_format)
    job_config = _get_import_package_job_config(build_file, package_format)

    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        from ros_buildfarm.jenkins import configure_job
        configure_job(jenkins, job_name, job_config, dry_run=dry_run)
    return (job_name, job_config)


def get_import_package_job_name(rosdistro_name, package_format):
    view_name = get_release_job_prefix(rosdistro_name)
    return '%s_import-package%s' % (
        view_name, '' if package_format == 'deb' else '-' + package_format)


def _get_import_package_job_config(build_file, package_format):
    template_name = 'release/%s/import_package_job.xml.em' % package_format
    job_data = {
        'target_queue': build_file.target_queue,
        'abi_incompatibility_assumed': build_file.abi_incompatibility_assumed,
        'notify_emails': build_file.notify_emails,
        'ros_buildfarm_repository': get_repository(),
        'credential_id': build_file.upload_credential_id,
        'dest_credential_id': build_file.upload_destination_credential_id,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


def configure_sync_packages_to_testing_job(
        config_url, rosdistro_name, release_build_name, os_name, os_code_name,
        arch, config=None, build_file=None, jenkins=None, dry_run=False):
    if config is None:
        config = get_config_index(config_url)
    if build_file is None:
        build_files = get_release_build_files(config, rosdistro_name)
        build_file = build_files[release_build_name]
    if jenkins is None:
        from ros_buildfarm.jenkins import connect
        jenkins = connect(config.jenkins_url)

    job_name = get_sync_packages_to_testing_job_name(
        rosdistro_name, os_name, os_code_name, arch)
    job_config = _get_sync_packages_to_testing_job_config(
        config_url, rosdistro_name, release_build_name, os_name, os_code_name,
        arch, config, build_file)

    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        from ros_buildfarm.jenkins import configure_job
        configure_job(jenkins, job_name, job_config, dry_run=dry_run)
    return (job_name, job_config)


def get_sync_packages_to_testing_job_name(
        rosdistro_name, os_name, os_code_name, arch):
    view_name = get_release_job_prefix(rosdistro_name)
    return '%s_sync-packages-to-testing%s_%s_%s' % (
        view_name, '' if package_format_mapping[os_name] == 'deb' else '_' + os_name,
        os_code_name, arch)


def _get_sync_packages_to_testing_job_config(
        config_url, rosdistro_name, release_build_name, os_name, os_code_name,
        arch, config, build_file):
    package_format = package_format_mapping[os_name]
    template_name = 'release/%s/sync_packages_to_testing_job.xml.em' % package_format

    repository_args, script_generating_key_files = \
        get_repositories_and_script_generating_key_files(build_file=build_file)

    job_data = {
        'ros_buildfarm_repository': get_repository(),

        'script_generating_key_files': script_generating_key_files,

        'config_url': config_url,
        'rosdistro_name': rosdistro_name,
        'release_build_name': release_build_name,
        'os_name': os_name,
        'os_code_name': os_code_name,
        'arch': arch,
        'repository_args': repository_args,

        'import_package_job_name': get_import_package_job_name(
            rosdistro_name, package_format),

        'notify_emails': build_file.notify_emails,
        'credential_id': build_file.upload_credential_id,
        'dest_credential_id': build_file.upload_destination_credential_id,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


def configure_sync_packages_to_main_job(
        config_url, rosdistro_name, release_build_name,
        config=None, build_file=None, jenkins=None, dry_run=False):
    if config is None:
        config = get_config_index(config_url)
    if build_file is None:
        build_files = get_release_build_files(config, rosdistro_name)
        build_file = build_files[release_build_name]
    if jenkins is None:
        from ros_buildfarm.jenkins import connect
        jenkins = connect(config.jenkins_url)

    package_formats = set(
        package_format_mapping[os_name] for os_name in build_file.targets.keys())
    assert len(package_formats) == 1
    package_format = package_formats.pop()

    job_name = get_sync_packages_to_main_job_name(
        rosdistro_name, package_format)
    job_config = _get_sync_packages_to_main_job_config(
        rosdistro_name, build_file, package_format)

    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        from ros_buildfarm.jenkins import configure_job
        configure_job(jenkins, job_name, job_config, dry_run=dry_run)
    return (job_name, job_config)


def get_sync_packages_to_main_job_name(rosdistro_name, package_format):
    view_name = get_release_job_prefix(rosdistro_name)
    return '%s_sync-packages-to-main%s' % (
        view_name, '' if package_format == 'deb' else '-' + package_format)


def _get_sync_packages_to_main_job_config(rosdistro_name, build_file, package_format):
    template_name = 'release/%s/sync_packages_to_main_job.xml.em' % package_format
    job_data = {
        'ros_buildfarm_repository': get_repository(),
        'rosdistro_name': rosdistro_name,

        'deb_sync_to_main_job_name': get_sync_packages_to_main_job_name(rosdistro_name, 'deb'),

        'notify_emails': build_file.notify_emails,
        'credential_id': build_file.upload_credential_id,
        'dest_credential_id': build_file.upload_destination_credential_id,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


def _get_maintainer_emails(cached_pkgs, pkg_name):
    maintainer_emails = set([])
    # add maintainers listed in latest release to recipients
    if cached_pkgs and pkg_name in cached_pkgs:
        for m in cached_pkgs[pkg_name].maintainers:
            maintainer_emails.add(m.email)
    return maintainer_emails


def partition_packages(
        config_url, rosdistro_name, release_build_name, target, cache_dir,
        deduplicate_dependencies=False, dist_cache=None):
    """Check all packages in the rosdistro and compare to the debian packages repository.

    Return the set of all packages and the set of missing ones.
    """
    # fetch debian package list
    config = get_config_index(config_url)
    index = get_index(config.rosdistro_index_url)
    dist_file = rosdistro_get_distribution_file(index, rosdistro_name)
    build_files = get_release_build_files(config, rosdistro_name)
    build_file = build_files[release_build_name]

    # Check that apt repos status
    repo_index = get_package_repo_data(
        build_file.target_repository, [target], cache_dir)[target]

    # for each release package which matches the release build file
    # check if a binary package exists
    binary_packages = set()
    all_pkg_names = dist_file.release_packages.keys()

    # Remove packages without versions declared.
    def get_package_version(dist_file, pkg_name):
        pkg = dist_file.release_packages[pkg_name]
        repo_name = pkg.repository_name
        repo = dist_file.repositories[repo_name]
        return repo.release_repository.version
    all_pkg_names = [p for p in all_pkg_names if get_package_version(dist_file, p)]

    distribution = get_cached_distribution(index, rosdistro_name, cache=dist_cache)
    pkg_names = filter_buildfile_packages_recursively(all_pkg_names, build_file, distribution)
    for pkg_name in sorted(pkg_names):
        debian_pkg_name = get_os_package_name(rosdistro_name, pkg_name)
        if debian_pkg_name in repo_index:
            binary_packages.add(pkg_name)

    # check that all elements from whitelist are present
    missing_binary_packages = set(pkg_names) - binary_packages

    if deduplicate_dependencies:
        # Do not list missing packages that are dependencies of other missing ones
        cached_pkgs = get_package_manifests(distribution)
        missing_binary_packages = filter_blocked_dependent_package_names(
            cached_pkgs,
            missing_binary_packages)

    return binary_packages, missing_binary_packages
