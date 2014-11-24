from datetime import datetime

from rosdistro import get_distribution_cache
from rosdistro import get_distribution_file
from rosdistro import get_index
from rosdistro import get_release_build_files

from ros_buildfarm.common import get_debian_package_name
from ros_buildfarm.common \
    import get_apt_mirrors_and_script_generating_key_files
from ros_buildfarm.common import get_release_view_name
from ros_buildfarm.common import JobValidationError
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_view
from ros_buildfarm.jenkins import connect
from ros_buildfarm.jenkins import JENKINS_MANAGEMENT_VIEW
from ros_buildfarm.templates import expand_template


def configure_release_jobs(
        rosdistro_index_url, rosdistro_name, release_build_name,
        append_timestamp=False):
    """
    Configure all Jenkins release jobs.

    L{configure_release_job} will be invoked for every package
    in the release repository and target which matches the
    build file criteria.
    """
    index = get_index(rosdistro_index_url)
    build_files = get_release_build_files(index, rosdistro_name)
    build_file = build_files[release_build_name]

    dist_cache = None
    if build_file.notify_maintainers or build_file.abi_incompatibility_assumed:
        dist_cache = get_distribution_cache(index, rosdistro_name)

    # get targets
    targets = []
    for os_name in build_file.get_target_os_names():
        for os_code_name in build_file.get_target_os_code_names(os_name):
            targets.append((os_name, os_code_name))
    print('The build file contains the following targets:')
    for os_name, os_code_name in targets:
        print('  - %s %s: %s' % (os_name, os_code_name, ', '.join(
            build_file.get_target_arches(os_name, os_code_name))))

    dist_file = get_distribution_file(index, rosdistro_name)

    jenkins = connect(build_file.jenkins_url)

    configure_import_package_job(
        rosdistro_index_url, rosdistro_name, release_build_name,
        index=index, build_file=build_file, jenkins=jenkins)

    view_name = get_release_view_name(rosdistro_name, release_build_name)
    view = configure_release_view(jenkins, view_name)

    pkg_names = dist_file.release_packages.keys()
    pkg_names = build_file.filter_packages(pkg_names)

    for pkg_name in sorted(pkg_names):
        pkg = dist_file.release_packages[pkg_name]
        repo_name = pkg.repository_name
        repo = dist_file.repositories[repo_name]
        if not repo.release_repository:
            print(("Skipping package '%s' in repository '%s': no release " +
                   "section") % (pkg_name, repo_name))
            continue
        if not repo.release_repository.version:
            print(("Skipping package '%s' in repository '%s': no release " +
                   "version") % (pkg_name, repo_name))
            continue

        for os_name, os_code_name in targets:
            configure_release_job(
                rosdistro_index_url, rosdistro_name, release_build_name,
                pkg_name, os_name, os_code_name,
                append_timestamp=append_timestamp,
                index=index, build_file=build_file, dist_file=dist_file,
                dist_cache=dist_cache, jenkins=jenkins, view=view,
                generate_import_package_job=False)


# Use a wrapper to transform JobValidationErrors into return values
def configure_release_job(*args, **kwargs):
    """
    Configure a Jenkins release job.

    The following jobs are created for each invocation:
    - N source deb job, one for each os_code_name
    - N*M binary debs, one for each (os_code_name, architecture) tuple
    """
    try:
        return configure_release_job_with_validation(*args, **kwargs)
    except JobValidationError as error:
        return error.message


def configure_release_job_with_validation(
        rosdistro_index_url, rosdistro_name, release_build_name,
        pkg_name, os_name, os_code_name, append_timestamp=False,
        index=None, build_file=None, dist_file=None, dist_cache=None,
        jenkins=None, view=None,
        generate_import_package_job=True,
        filter_arches=None):
    if index is None:
        index = get_index(rosdistro_index_url)
    if build_file is None:
        build_files = get_release_build_files(index, rosdistro_name)
        build_file = build_files[release_build_name]
    if dist_file is None:
        dist_file = get_distribution_file(index, rosdistro_name)

    pkg_names = dist_file.release_packages.keys()
    pkg_names = build_file.filter_packages(pkg_names)

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

    if os_name not in build_file.get_target_os_names():
        raise JobValidationError(
            "Invalid OS name '%s' " % os_name +
            'choose one of the following: ' +
            ', '.join(sorted(build_file.get_target_os_names())))

    if os_code_name not in build_file.get_target_os_code_names(os_name):
        raise JobValidationError(
            "Invalid OS code name '%s' " % os_code_name +
            'choose one of the following: ' +
            ', '.join(sorted(build_file.get_target_os_code_names(os_name))))

    if dist_cache is None and \
            (build_file.notify_maintainers or
             build_file.abi_incompatibility_assumed):
        dist_cache = get_distribution_cache(index, rosdistro_name)
    if jenkins is None:
        jenkins = connect(build_file.jenkins_url)
    if view is None:
        view_name = get_release_view_name(rosdistro_name, release_build_name)
        configure_release_view(jenkins, view_name)

    if generate_import_package_job:
        configure_import_package_job(
            rosdistro_index_url, rosdistro_name, release_build_name,
            index=index, build_file=build_file, jenkins=jenkins)

    # sourcedeb job
    conf = build_file.get_target_configuration(
        os_name=os_name, os_code_name=os_code_name)

    job_name = get_sourcedeb_job_name(
        rosdistro_name, release_build_name,
        pkg_name, os_name, os_code_name)

    job_config = _get_sourcedeb_job_config(
        rosdistro_index_url, rosdistro_name, release_build_name,
        build_file, os_name, os_code_name, conf, _get_target_arches(
            build_file, os_name, os_code_name, print_skipped=False),
        repo.release_repository, pkg_name,
        repo_name, dist_cache=dist_cache)
    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        configure_job(jenkins, job_name, job_config)

    dependency_names = []
    if build_file.abi_incompatibility_assumed:
        dependency_names = _get_direct_dependencies(
            pkg_name, dist_cache, pkg_names)
        if dependency_names is None:
            return

    # binarydeb jobs
    for arch in _get_target_arches(build_file, os_name, os_code_name):
        if filter_arches and arch not in filter_arches:
            continue

        conf = build_file.get_target_configuration(
            os_name=os_name, os_code_name=os_code_name, arch=arch)

        job_name = get_binarydeb_job_name(
            rosdistro_name, release_build_name,
            pkg_name, os_name, os_code_name, arch)

        upstream_job_names = [
            get_binarydeb_job_name(
                rosdistro_name, release_build_name,
                dependency_name, os_name, os_code_name, arch)
            for dependency_name in dependency_names]

        job_config = _get_binarydeb_job_config(
            rosdistro_index_url, rosdistro_name, release_build_name,
            build_file, os_name, os_code_name, arch, conf,
            repo.release_repository, pkg_name, append_timestamp,
            repo_name, dist_cache=dist_cache,
            upstream_job_names=upstream_job_names)
        # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
        if isinstance(jenkins, object) and jenkins is not False:
            configure_job(jenkins, job_name, job_config)


def configure_release_view(jenkins, view_name):
    return configure_view(
        jenkins, view_name, include_regex='%s__.+' % view_name)


def get_sourcedeb_job_name(rosdistro_name, release_build_name,
                           pkg_name, os_name, os_code_name):
    view_name = get_release_view_name(rosdistro_name, release_build_name)
    return '%s__%s__%s_%s__source' % \
        (view_name, pkg_name, os_name, os_code_name)


def _get_target_arches(build_file, os_name, os_code_name, print_skipped=True):
    arches = []
    for arch in build_file.get_target_arches(os_name, os_code_name):
        # TODO support for non amd64 arch missing
        if arch not in ['amd64']:
            if print_skipped:
                print('Skipping arch:', arch)
            continue
        arches.append(arch)
    return arches


def get_binarydeb_job_name(rosdistro_name, release_build_name,
                           pkg_name, os_name, os_code_name, arch):
    view_name = get_release_view_name(rosdistro_name, release_build_name)
    return '%s__%s__%s_%s_%s__binary' % \
        (view_name, pkg_name, os_name, os_code_name, arch)


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
        rosdistro_index_url, rosdistro_name, release_build_name,
        build_file, os_name, os_code_name, conf, binary_arches,
        release_repo_spec, pkg_name,
        repo_name, dist_cache=None):
    template_name = 'release/sourcedeb_job.xml.em'
    now = datetime.utcnow()
    now_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    apt_mirror_args, script_generating_key_files = \
        get_apt_mirrors_and_script_generating_key_files(conf)

    sourcedeb_files = [
        'sourcedeb/*.debian.tar.gz',
        'sourcedeb/*.dsc',
        'sourcedeb/*.orig.tar.gz',
        'sourcedeb/*_source.changes',
    ]

    binary_job_names = [
        get_binarydeb_job_name(
            rosdistro_name, release_build_name,
            pkg_name, os_name, os_code_name, arch)
        for arch in binary_arches]

    maintainer_emails = get_maintainer_emails(dist_cache, repo_name) \
        if build_file.notify_maintainers \
        else set([])

    job_data = {
        'template_name': template_name,
        'now_str': now_str,

        'job_priority': build_file.jenkins_job_priority,

        'release_repo_spec': release_repo_spec,

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_index_url': rosdistro_index_url,
        'rosdistro_name': rosdistro_name,
        'release_build_name': release_build_name,
        'pkg_name': pkg_name,
        'os_name': os_name,
        'os_code_name': os_code_name,
        'apt_mirror_args': apt_mirror_args,

        'sourcedeb_files': sourcedeb_files,

        'import_package_job_name': get_import_package_job_name(
            rosdistro_name, release_build_name),
        'debian_package_name': get_debian_package_name(
            rosdistro_name, pkg_name),

        'child_projects': binary_job_names,

        'notify_emails': build_file.notify_emails,
        'maintainer_emails': maintainer_emails,
        'notify_maintainers': build_file.notify_maintainers,

        'timeout_minutes': build_file.jenkins_sourcedeb_job_timeout,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


def _get_binarydeb_job_config(
        rosdistro_index_url, rosdistro_name, release_build_name,
        build_file, os_name, os_code_name, arch, conf,
        release_repo_spec, pkg_name, append_timestamp,
        repo_name, dist_cache=None, upstream_job_names=None):
    template_name = 'release/binarydeb_job.xml.em'
    now = datetime.utcnow()
    now_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    apt_mirror_args, script_generating_key_files = \
        get_apt_mirrors_and_script_generating_key_files(conf)

    binarydeb_files = [
        'binarydeb/*.changes',
        'binarydeb/*.deb',
    ]

    maintainer_emails = get_maintainer_emails(dist_cache, repo_name) \
        if build_file.notify_maintainers \
        else set([])

    job_data = {
        'template_name': template_name,
        'now_str': now_str,

        'job_priority': build_file.jenkins_job_priority,

        'upstream_projects': upstream_job_names,

        'release_repo_spec': release_repo_spec,

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_index_url': rosdistro_index_url,
        'rosdistro_name': rosdistro_name,
        'release_build_name': release_build_name,
        'pkg_name': pkg_name,
        'os_name': os_name,
        'os_code_name': os_code_name,
        'arch': arch,
        'apt_mirror_args': apt_mirror_args,

        'append_timestamp': append_timestamp,

        'binarydeb_files': binarydeb_files,

        'import_package_job_name': get_import_package_job_name(
            rosdistro_name, release_build_name),
        'debian_package_name': get_debian_package_name(
            rosdistro_name, pkg_name),

        'notify_emails': build_file.notify_emails,
        'maintainer_emails': maintainer_emails,
        'notify_maintainers': build_file.notify_maintainers,

        'timeout_minutes': build_file.jenkins_binarydeb_job_timeout,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


def configure_import_package_job(
        rosdistro_index_url, rosdistro_name, release_build_name,
        index=None, build_file=None, jenkins=None):
    if index is None:
        index = get_index(rosdistro_index_url)
    if build_file is None:
        build_files = get_release_build_files(index, rosdistro_name)
        build_file = build_files[release_build_name]
    if jenkins is None:
        jenkins = connect(build_file.jenkins_url)

    job_name = get_import_package_job_name(rosdistro_name, release_build_name)
    job_config = _get_import_package_job_config(build_file)
    view = configure_view(jenkins, JENKINS_MANAGEMENT_VIEW)

    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        configure_job(jenkins, job_name, job_config, view)


def get_import_package_job_name(rosdistro_name, release_build_name):
    view_name = get_release_view_name(rosdistro_name, release_build_name)
    return '%s_import_package' % view_name


def _get_import_package_job_config(build_file):
    template_name = 'release/import_package_job.xml.em'
    now = datetime.utcnow()
    now_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    job_data = {
        'template_name': template_name,
        'now_str': now_str,

        'notify_emails': build_file.notify_emails,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


def get_maintainer_emails(dist_cache, repo_name):
    maintainer_emails = set([])
    if dist_cache and repo_name in dist_cache.distribution_file.repositories:
        from catkin_pkg.package import parse_package_string
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
    return maintainer_emails
