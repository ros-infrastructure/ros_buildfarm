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

from rosdistro import get_distribution_cache
from rosdistro import get_index

from ros_buildfarm.common import get_binarydeb_job_name
from ros_buildfarm.common import get_debian_package_name
from ros_buildfarm.common import get_default_node_label
from ros_buildfarm.common import get_github_project_url
from ros_buildfarm.common import get_node_label
from ros_buildfarm.common import get_release_binary_view_name
from ros_buildfarm.common import get_release_job_prefix
from ros_buildfarm.common import get_release_source_view_name
from ros_buildfarm.common import get_release_view_name
from ros_buildfarm.common \
    import get_repositories_and_script_generating_key_files
from ros_buildfarm.common import get_sourcedeb_job_name
from ros_buildfarm.common import get_system_architecture
from ros_buildfarm.common import JobValidationError
from ros_buildfarm.common import write_groovy_script_and_configs
from ros_buildfarm.config import get_distribution_file
from ros_buildfarm.config import get_index as get_config_index
from ros_buildfarm.config import get_release_build_files
from ros_buildfarm.git import get_repository
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_view
from ros_buildfarm.jenkins import connect
from ros_buildfarm.jenkins import remove_jobs
from ros_buildfarm.templates import expand_template


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
    filtered_pkg_names = build_file.filter_packages(pkg_names)
    explicitly_ignored_pkg_names = set(pkg_names) - set(filtered_pkg_names)
    if explicitly_ignored_pkg_names:
        print(('The following packages are being %s because of ' +
               'white-/blacklisting:') %
              ('ignored' if build_file.skip_ignored_packages else 'disabled'))
        for pkg_name in sorted(explicitly_ignored_pkg_names):
            print('  -', pkg_name)

    dist_cache = get_distribution_cache(index, rosdistro_name)

    if explicitly_ignored_pkg_names:
        # get direct dependencies from distro cache for each package
        direct_dependencies = {}
        for pkg_name in pkg_names:
            direct_dependencies[pkg_name] = _get_direct_dependencies(
                pkg_name, dist_cache, pkg_names) or set([])

        # find recursive downstream deps for all explicitly ignored packages
        ignored_pkg_names = set(explicitly_ignored_pkg_names)
        while True:
            implicitly_ignored_pkg_names = _get_downstream_package_names(
                ignored_pkg_names, direct_dependencies)
            if implicitly_ignored_pkg_names - ignored_pkg_names:
                ignored_pkg_names |= implicitly_ignored_pkg_names
                continue
            break
        implicitly_ignored_pkg_names = \
            ignored_pkg_names - explicitly_ignored_pkg_names

        if implicitly_ignored_pkg_names:
            print(('The following packages are being %s because their ' +
                   'dependencies are being ignored:') % ('ignored'
                  if build_file.skip_ignored_packages else 'disabled'))
            for pkg_name in sorted(implicitly_ignored_pkg_names):
                print('  -', pkg_name)
            filtered_pkg_names = \
                set(filtered_pkg_names) - implicitly_ignored_pkg_names

    # all further configuration will be handled by either the Jenkins API
    # or by a generated groovy script
    jenkins = connect(config.jenkins_url) if groovy_script is None else False

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
                os_code_name, arch,
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
    from catkin_pkg.package import parse_package_string
    from ros_buildfarm.common import topological_order_packages
    pkgs = {}
    for pkg_name in pkg_names:
        if pkg_name not in dist_cache.release_package_xmls:
            print("Skipping package '%s': no released package.xml in cache" %
                  (pkg_name), file=sys.stderr)
            continue
        pkg_xml = dist_cache.release_package_xmls[pkg_name]
        pkg = parse_package_string(pkg_xml)
        pkgs[pkg_name] = pkg
    ordered_pkg_tuples = topological_order_packages(pkgs)

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
                        dist_cache=dist_cache,
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


def _get_downstream_package_names(pkg_names, dependencies):
    downstream_pkg_names = set([])
    for pkg_name, deps in dependencies.items():
        if deps.intersection(pkg_names):
            downstream_pkg_names.add(pkg_name)
    return downstream_pkg_names


# Configure a Jenkins release job which consists of
# - a source deb job
# - N binary debs, one for each archicture
def configure_release_job(
        config_url, rosdistro_name, release_build_name,
        pkg_name, os_name, os_code_name,
        config=None, build_file=None,
        index=None, dist_file=None, dist_cache=None,
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

    if dist_cache is None and \
            (build_file.notify_maintainers or
             build_file.abi_incompatibility_assumed):
        dist_cache = get_distribution_cache(index, rosdistro_name)
    if jenkins is None:
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
                os_code_name, arch,
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
        pkg_name, repo_name, repo.release_repository, dist_cache=dist_cache,
        is_disabled=is_source_disabled,
        other_build_files_same_platform=other_build_files_same_platform)
    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        configure_job(jenkins, source_job_name, job_config, dry_run=dry_run)
    source_job_names.append(source_job_name)
    job_configs[source_job_name] = job_config

    dependency_names = []
    if build_file.abi_incompatibility_assumed:
        dependency_names = _get_direct_dependencies(
            pkg_name, dist_cache, pkg_names)
        # if dependencies are not yet available in rosdistro cache
        # skip binary jobs
        if dependency_names is None:
            print(("Skipping binary jobs for package '%s' because it is not " +
                   "yet in the rosdistro cache") % pkg_name, file=sys.stderr)
            return source_job_names, binary_job_names, job_configs

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
            dist_cache=dist_cache, upstream_job_names=upstream_job_names,
            is_disabled=is_disabled)
        # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
        if isinstance(jenkins, object) and jenkins is not False:
            configure_job(jenkins, job_name, job_config, dry_run=dry_run)
        binary_job_names.append(job_name)
        job_configs[job_name] = job_config

    return source_job_names, binary_job_names, job_configs


def configure_release_views(
        jenkins, rosdistro_name, release_build_name, targets, dry_run=False):
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


def _get_direct_dependencies(pkg_name, dist_cache, pkg_names):
    from catkin_pkg.package import parse_package_string
    if pkg_name not in dist_cache.release_package_xmls:
        return None
    pkg_xml = dist_cache.release_package_xmls[pkg_name]
    pkg = parse_package_string(pkg_xml)
    depends = set([
        d.name for d in (
            pkg.buildtool_depends +
            pkg.build_depends +
            pkg.buildtool_export_depends +
            pkg.build_export_depends +
            pkg.exec_depends +
            pkg.test_depends)
        if d.name in pkg_names])
    return depends


def _get_sourcedeb_job_config(
        config_url, rosdistro_name, release_build_name,
        config, build_file, os_name, os_code_name,
        pkg_name, repo_name, release_repository, dist_cache=None,
        is_disabled=False, other_build_files_same_platform=None):
    template_name = 'release/sourcedeb_job.xml.em'

    repository_args, script_generating_key_files = \
        get_repositories_and_script_generating_key_files(build_file=build_file)

    sourcedeb_files = [
        'sourcedeb/*.debian.tar.gz',
        'sourcedeb/*.debian.tar.xz',
        'sourcedeb/*.dsc',
        'sourcedeb/*.orig.tar.gz',
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

    maintainer_emails = _get_maintainer_emails(dist_cache, pkg_name) \
        if notify_maintainers \
        else set([])

    job_data = {
        'github_url': get_github_project_url(release_repository.url),

        'job_priority': build_file.jenkins_source_job_priority,
        'node_label': get_node_label(
            build_file.jenkins_source_job_label,
            get_default_node_label('%s_%s' % (
                rosdistro_name, 'sourcedeb'))),

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

        'import_package_job_name': get_import_package_job_name(rosdistro_name),
        'debian_package_name': get_debian_package_name(
            rosdistro_name, pkg_name),

        'notify_emails': notify_emails,
        'maintainer_emails': maintainer_emails,
        'notify_maintainers': notify_maintainers,

        'timeout_minutes': build_file.jenkins_source_job_timeout,

        'credential_id': build_file.upload_credential_id,

        'git_ssh_credential_id': config.git_ssh_credential_id,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


def _get_binarydeb_job_config(
        config_url, rosdistro_name, release_build_name,
        config, build_file, os_name, os_code_name, arch,
        pkg_name, repo_name, release_repository,
        dist_cache=None, upstream_job_names=None,
        is_disabled=False):
    template_name = 'release/binarydeb_job.xml.em'

    repository_args, script_generating_key_files = \
        get_repositories_and_script_generating_key_files(build_file=build_file)
    repository_args.append(
        '--target-repository ' + build_file.target_repository)

    binarydeb_files = [
        'binarydeb/*.changes',
        'binarydeb/*.deb',
    ]

    sync_to_testing_job_name = [get_sync_packages_to_testing_job_name(
        rosdistro_name, os_code_name, arch)]

    maintainer_emails = _get_maintainer_emails(dist_cache, pkg_name) \
        if build_file.notify_maintainers \
        else set([])

    job_data = {
        'github_url': get_github_project_url(release_repository.url),

        'job_priority': build_file.jenkins_binary_job_priority,
        'node_label': get_node_label(
            build_file.jenkins_binary_job_label,
            get_default_node_label('%s_%s_%s' % (
                rosdistro_name, 'binarydeb', release_build_name))),

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

        'import_package_job_name': get_import_package_job_name(rosdistro_name),
        'debian_package_name': get_debian_package_name(
            rosdistro_name, pkg_name),

        'child_projects': sync_to_testing_job_name,

        'notify_emails': build_file.notify_emails,
        'maintainer_emails': maintainer_emails,
        'notify_maintainers': build_file.notify_maintainers,

        'timeout_minutes': build_file.jenkins_binary_job_timeout,

        'credential_id': build_file.upload_credential_id,
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
        jenkins = connect(config.jenkins_url)

    job_name = get_import_package_job_name(rosdistro_name)
    job_config = _get_import_package_job_config(build_file)

    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        configure_job(jenkins, job_name, job_config, dry_run=dry_run)
    return (job_name, job_config)


def get_import_package_job_name(rosdistro_name):
    view_name = get_release_job_prefix(rosdistro_name)
    return '%s_import-package' % view_name


def _get_import_package_job_config(build_file):
    template_name = 'release/import_package_job.xml.em'
    job_data = {
        'target_queue': build_file.target_queue,
        'abi_incompatibility_assumed': build_file.abi_incompatibility_assumed,
        'notify_emails': build_file.notify_emails,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


def configure_sync_packages_to_testing_job(
        config_url, rosdistro_name, release_build_name, os_code_name, arch,
        config=None, build_file=None, jenkins=None, dry_run=False):
    if config is None:
        config = get_config_index(config_url)
    if build_file is None:
        build_files = get_release_build_files(config, rosdistro_name)
        build_file = build_files[release_build_name]
    if jenkins is None:
        jenkins = connect(config.jenkins_url)

    job_name = get_sync_packages_to_testing_job_name(
        rosdistro_name, os_code_name, arch)
    job_config = _get_sync_packages_to_testing_job_config(
        config_url, rosdistro_name, release_build_name, os_code_name, arch,
        config, build_file)

    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        configure_job(jenkins, job_name, job_config, dry_run=dry_run)
    return (job_name, job_config)


def get_sync_packages_to_testing_job_name(
        rosdistro_name, os_code_name, arch):
    view_name = get_release_job_prefix(rosdistro_name)
    return '%s_sync-packages-to-testing_%s_%s' % \
        (view_name, os_code_name, arch)


def _get_sync_packages_to_testing_job_config(
        config_url, rosdistro_name, release_build_name, os_code_name, arch,
        config, build_file):
    template_name = 'release/sync_packages_to_testing_job.xml.em'

    repository_args, script_generating_key_files = \
        get_repositories_and_script_generating_key_files(build_file=build_file)

    job_data = {
        'ros_buildfarm_repository': get_repository(),

        'script_generating_key_files': script_generating_key_files,

        'config_url': config_url,
        'rosdistro_name': rosdistro_name,
        'release_build_name': release_build_name,
        'os_code_name': os_code_name,
        'arch': arch,
        'repository_args': repository_args,

        'notify_emails': build_file.notify_emails,
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
        jenkins = connect(config.jenkins_url)

    job_name = get_sync_packages_to_main_job_name(
        rosdistro_name)
    job_config = _get_sync_packages_to_main_job_config(
        rosdistro_name, build_file)

    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        configure_job(jenkins, job_name, job_config, dry_run=dry_run)
    return (job_name, job_config)


def get_sync_packages_to_main_job_name(rosdistro_name):
    view_name = get_release_job_prefix(rosdistro_name)
    return '%s_sync-packages-to-main' % view_name


def _get_sync_packages_to_main_job_config(rosdistro_name, build_file):
    template_name = 'release/sync_packages_to_main_job.xml.em'
    job_data = {
        'rosdistro_name': rosdistro_name,

        'notify_emails': build_file.notify_emails,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


def _get_maintainer_emails(dist_cache, pkg_name):
    maintainer_emails = set([])
    # add maintainers listed in latest release to recipients
    if dist_cache and pkg_name in dist_cache.release_package_xmls:
        from catkin_pkg.package import parse_package_string
        pkg_xml = dist_cache.release_package_xmls[pkg_name]
        pkg = parse_package_string(pkg_xml)
        for m in pkg.maintainers:
            maintainer_emails.add(m.email)
    return maintainer_emails
