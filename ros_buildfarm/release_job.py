from datetime import datetime

from jenkinsapi.jenkins import Jenkins
from rosdistro.repository import Repository

from ros_buildfarm.build_configuration import BuildConfiguration
from ros_buildfarm.build_configuration import PackageInfo
from ros_buildfarm.build_configuration import ReleaseBuildConfiguration
from ros_buildfarm.common \
    import get_apt_mirrors_and_script_generating_key_files
from ros_buildfarm.common import get_debian_package_name
from ros_buildfarm.common import get_release_view_name
from ros_buildfarm.common import JobValidationError
from ros_buildfarm.common import OSArchTarget
from ros_buildfarm.common import OSTarget
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_view
from ros_buildfarm.jenkins import connect
from ros_buildfarm.jenkins import JENKINS_MANAGEMENT_VIEW
from ros_buildfarm.templates import expand_template


def configure_release_jobs(build_cfg: BuildConfiguration):
    """
    For every package in the release repository and target
    which matches the build file criteria invoke configure_release_job().

    @param build_cfg: Configuration for this build. Likely based on command line arguments.
    """

    # Load the index.yaml file
    config = build_cfg.resolve()

    # get targets
    targets = config.get_target_os()
    print_os_targets(config, targets)

    # Configure the import package job
    jenkins = connect(config.build_file.jenkins_url)
    configure_import_package_job(config, jenkins=jenkins)

    view_name = get_release_view_name(config.base.rosdistro_name, config.base.release_build_name)
    view = configure_release_view(jenkins, view_name)

    for pkg_name in sorted(config.get_package_names()):
        for os_target in targets:
            result = configure_release_job(
                config, pkg_name, os_target,
                jenkins=jenkins, view=view,
                generate_import_package_job=False)
            if result is None:
                print("Skipping package '%s':" % pkg_name)


def print_os_targets(cfg, targets):
    print('The build file contains the following targets:')
    for os_target in targets:
        print('  - %s: %s' % (os_target, ', '.join(cfg.get_target_architectures_by_os(os_target))))


def verify_is_release_repository(repo: Repository):
    if not repo.release_repository:
        raise JobValidationError("Repository '%s' has no release section" % repo.name)

    if not repo.release_repository.version:
        raise JobValidationError("Repository '%s' has no release version" % repo.name)


# Use a wrapper to transform JobValidationErrors into return values
def configure_release_job(*args, **kwargs):
    try:
        return configure_release_job_with_validation(*args, **kwargs)
    except JobValidationError as error:
        return error.message


def configure_release_job_with_validation(config: ReleaseBuildConfiguration,
                                          pkg_name: str, os_target: OSTarget,
                                          jenkins=None, view=None,
                                          generate_import_package_job=True,
                                          filter_arches=None):
    """
    Configure a Jenkins release job which consists of
    - a source deb job
    - N binary debs, one for each architecture
    """
    config.verify_contains_package(pkg_name)
    config.verify_target_os(os_target)

    pkg_info = config.get_package_info(pkg_name)
    verify_is_release_repository(pkg_info.repo)

    if jenkins is None:
        jenkins = connect(config.build_file.jenkins_url)

    if view is None:
        view_name = get_release_view_name(config.base.rosdistro_name, config.base.release_build_name)
        configure_release_view(jenkins, view_name)

    # IMPORT:
    if generate_import_package_job:
        configure_import_package_job(config, jenkins=jenkins)

    # SOURCES: Create one sourcedeb job per package
    _configure_sourcedeb_job(config, os_target, pkg_info,
                             jenkins=jenkins)

    # BINARIES: Create one binarydeb job per package and architecture
    _configure_binarydeb_jobs(config, os_target, filter_arches, pkg_info,
                              jenkins=jenkins)


def _configure_sourcedeb_job(config: ReleaseBuildConfiguration, os_target: OSTarget,
                             pkg_info: PackageInfo, jenkins):
    target_config = config.get_target_configuration(os_target)
    target_architectures = config.get_filtered_target_architectures_by_os(os_target, print_skipped=False)

    job_name = _get_sourcedeb_job_name(config.base, os_target, pkg_info.pkg_name)
    job_config = _get_sourcedeb_job_config(config, os_target, target_config, target_architectures, pkg_info)

    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        configure_job(jenkins, job_name, job_config)


def _get_sourcedeb_job_name(build_cfg: BuildConfiguration, os_target: OSTarget, pkg_name: str) -> str:
    return get_sourcedeb_job_name(build_cfg.rosdistro_name,
                                  build_cfg.release_build_name,
                                  pkg_name, os_target.os_name, os_target.os_code_name)


# Temporary wrapper until the other API clients of get_sourcedeb_job_name are migrated
def get_sourcedeb_job_name(rosdistro_name, release_build_name,
                           pkg_name, os_name, os_code_name):
    view_name = get_release_view_name(rosdistro_name, release_build_name)
    return '%s__%s__%s_%s__source' % \
           (view_name, pkg_name, os_name, os_code_name)


def _configure_binarydeb_jobs(config, os_target, filter_arches, pkg_info, jenkins):
    dependency_names = []
    if config.build_file.abi_incompatibility_assumed:
        dependency_names = config.get_direct_dependencies(pkg_info.pkg_name)
        if dependency_names is None:
            return

    for arch in config.get_filtered_target_architectures_by_os(os_target):
        if filter_arches and arch not in filter_arches:
            continue

        os_arch_target = OSArchTarget(os_target, arch)
        target_config = config.get_target_configuration(os_arch_target)
        job_name = _get_binarydeb_job_name(config.base, pkg_info.pkg_name, os_arch_target)

        upstream_job_names = [
            _get_binarydeb_job_name(config.base, dependency_name, os_arch_target)
            for dependency_name in dependency_names]

        job_config = _get_binarydeb_job_config(
            config, os_arch_target, target_config,
            pkg_info, upstream_job_names=upstream_job_names)

        # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
        if isinstance(jenkins, object) and jenkins is not False:
            configure_job(jenkins, job_name, job_config)


def configure_release_view(jenkins, view_name):
    return configure_view(
        jenkins, view_name, include_regex='%s__.+' % view_name)


# Temporary wrapper until the other API clients of get_binarydeb_job_name are migrated
def _get_binarydeb_job_name(build_cfg: BuildConfiguration, pkg_name: str, target: OSArchTarget):
    return get_binarydeb_job_name(build_cfg.rosdistro_name, build_cfg.release_build_name,
                                  pkg_name, target.os_name, target.os_code_name, target.arch)


def get_binarydeb_job_name(rosdistro_name, release_build_name,
                           pkg_name, os_name, os_code_name, arch):
    view_name = get_release_view_name(rosdistro_name, release_build_name)
    return '%s__%s__%s_%s_%s__binary' % \
           (view_name, pkg_name, os_name, os_code_name, arch)


def _get_sourcedeb_job_config(
        config: ReleaseBuildConfiguration,
        os_target: OSTarget,
        target_config: dict,
        binary_arches: list,
        pkg_info: PackageInfo):
    template_name = 'release/sourcedeb_job.xml.em'
    now = datetime.utcnow()
    now_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    apt_mirror_args, script_generating_key_files = \
        get_apt_mirrors_and_script_generating_key_files(target_config)

    sourcedeb_files = [
        'sourcedeb/*.debian.tar.gz',
        'sourcedeb/*.dsc',
        'sourcedeb/*.orig.tar.gz',
        'sourcedeb/*_source.changes',
    ]

    binary_job_names = [
        _get_binarydeb_job_name(config.base, pkg_info.pkg_name, OSArchTarget(os_target, arch))
        for arch in binary_arches]

    job_data = {
        'template_name': template_name,
        'now_str': now_str,

        'job_priority': config.build_file.jenkins_job_priority,

        'release_repo_spec': pkg_info.release_repository,

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_index_url': config.base.rosdistro_index_url,
        'rosdistro_name': config.base.rosdistro_name,
        'release_build_name': config.base.release_build_name,
        'pkg_name': pkg_info.pkg_name,
        'os_name': os_target.os_name,
        'os_code_name': os_target.os_code_name,
        'apt_mirror_args': apt_mirror_args,

        'sourcedeb_files': sourcedeb_files,

        'import_package_job_name': _get_import_package_job_name(config.base),
        'debian_package_name': get_debian_package_name(config.base, pkg_info.pkg_name),

        'child_projects': binary_job_names,

        'notify_emails': config.build_file.notify_emails,
        'maintainer_emails': config.get_maintainer_emails(pkg_info.repo_name),
        'notify_maintainers': config.build_file.notify_maintainers,

        'timeout_minutes': config.build_file.jenkins_sourcedeb_job_timeout,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


def _get_binarydeb_job_config(config: ReleaseBuildConfiguration, os_arch_target: OSArchTarget, conf,
                              pkg_info: PackageInfo, upstream_job_names=None):
    template_name = 'release/binarydeb_job.xml.em'
    now = datetime.utcnow()
    now_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    apt_mirror_args, script_generating_key_files = \
        get_apt_mirrors_and_script_generating_key_files(conf)

    binarydeb_files = [
        'binarydeb/*.changes',
        'binarydeb/*.deb',
    ]

    job_data = {
        'template_name': template_name,
        'now_str': now_str,

        'job_priority': config.build_file.jenkins_job_priority,

        'upstream_projects': upstream_job_names,

        'release_repo_spec': pkg_info.release_repository,

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_index_url': config.base.rosdistro_index_url,
        'rosdistro_name': config.base.rosdistro_name,
        'release_build_name': config.base.release_build_name,
        'pkg_name': pkg_info.pkg_name,
        'os_name': os_arch_target.os_name,
        'os_code_name': os_arch_target.os_code_name,
        'arch': os_arch_target.arch,
        'apt_mirror_args': apt_mirror_args,

        'append_timestamp': config.base.append_timestamp,

        'binarydeb_files': binarydeb_files,

        'import_package_job_name': _get_import_package_job_name(config.base),
        'debian_package_name': _get_debian_package_name(config.base, pkg_info.pkg_name),

        'notify_emails': config.build_file.notify_emails,
        'maintainer_emails': config.get_maintainer_emails_to_notify(pkg_info.repo_name),
        'notify_maintainers': config.build_file.notify_maintainers,

        'timeout_minutes': config.build_file.jenkins_binarydeb_job_timeout,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


def configure_import_package_job(cfg: ReleaseBuildConfiguration, jenkins: Jenkins):
    job_name = get_import_package_job_name(cfg.base.rosdistro_name, cfg.base.release_build_name)
    job_config = _get_import_package_job_config(cfg.build_file)
    view = configure_view(jenkins, JENKINS_MANAGEMENT_VIEW)

    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        configure_job(jenkins, job_name, job_config, view)


# Temporary wrapper until the other API clients of get_import_package_job_name are migrated
def _get_import_package_job_name(build_cfg: BuildConfiguration):
    return get_import_package_job_name(build_cfg.rosdistro_name, build_cfg.release_build_name)


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


# Temporary wrappers:
def _get_debian_package_name(build_cfg: BuildConfiguration, pkg_name):
    return get_debian_package_name(build_cfg.rosdistro_name, pkg_name)


# Temporary wrapper
def _get_release_view_name(build_cfg: BuildConfiguration):
    return get_release_view_name(build_cfg.rosdistro_name, build_cfg.release_build_name)
