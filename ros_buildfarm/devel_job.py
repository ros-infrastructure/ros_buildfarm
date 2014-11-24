from datetime import datetime

from ros_buildfarm.build_configuration import BuildConfiguration
from ros_buildfarm.build_configuration import BuildType
from ros_buildfarm.build_configuration import SourceBuildConfiguration
from ros_buildfarm.common \
    import get_apt_mirrors_and_script_generating_key_files
from ros_buildfarm.common import get_devel_view_name
from ros_buildfarm.common import OSArchTarget
from ros_buildfarm.git import get_ros_buildfarm_url
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_view
from ros_buildfarm.templates import expand_template


def configure_devel_jobs(build_cfg: BuildConfiguration):
    """
    Configure all available devel jobs.

    For every source repository and target which matches the
    build file criteria invoke configure_devel_job().
    """
    config = build_cfg.resolve(build_type=BuildType.source)

    # get targets
    targets = config.get_os_architecture_targets()
    print_os_architecture_targets(targets)

    jenkins = config.connect_to_jenkins()

    view_name = get_devel_view_name(config.base.rosdistro_name, config.base.source_build_name)
    view = configure_devel_view(jenkins, view_name)

    for repo_name in sorted(config.get_filtered_repositories()):
        repo = config.dist_file.repositories[repo_name]
        if not repo.source_repository:
            print("Skipping repository '%s': no source section" % repo_name)
            continue

        if not repo.source_repository.version:
            print("Skipping repository '%s': no source version" % repo_name)
            continue

        for os_arch_target in targets:
            configure_devel_job(
                config, repo_name, os_arch_target,
                jenkins=jenkins, view=view
            )


def print_os_architecture_targets(targets):
    print('The build file contains the following targets:')
    for os_arch_target in targets:
        print('  -',
              os_arch_target.os_name,
              os_arch_target.os_code_name,
              os_arch_target.arch)


def configure_devel_job(
        config: SourceBuildConfiguration,
        repo_name,
        os_arch_target: OSArchTarget,
        jenkins=None, view=None):
    """
    Configure a single Jenkins devel job.

    This includes the following steps:
    - clone the source repository to use
    - clone the ros_buildfarm repository
    - write the distribution repository keys into files
    - invoke the run_devel_job script
    """

    config.verify_repository_name(repo_name)

    repo = config.dist_file.repositories[repo_name]

    if not repo.source_repository:
        return "Repository '%s' has no source section" % repo_name
    if not repo.source_repository.version:
        return "Repository '%s' has no source version" % repo_name

    config.verify_target_os_architecture(os_arch_target)

    if jenkins is None:
        jenkins = config.connect_to_jenkins()
    if view is None:
        view_name = get_devel_view_name(config.base.rosdistro_name, config.base.source_build_name)
        configure_devel_view(jenkins, view_name)

    conf = config.get_target_configuration(os_arch_target)

    job_name = _get_devel_job_name(config.base, repo_name, os_arch_target)
    job_config = _get_devel_job_config(
        config, os_arch_target, conf, repo.source_repository, repo_name)

    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        configure_job(jenkins, job_name, job_config)


# Temporary wrapper until the other API clients of get_devel_job_name are migrated
def _get_devel_job_name(build_cfg: BuildConfiguration,
                        repo_name, os_arch_target: OSArchTarget):
    return get_devel_job_name(build_cfg.rosdistro_name, build_cfg.source_build_name,
                              repo_name,
                              os_arch_target.os_name,
                              os_arch_target.os_code_name,
                              os_arch_target.arch)


def get_devel_job_name(rosdistro_name, source_build_name,
                       repo_name, os_name, os_code_name, arch):
    view_name = get_devel_view_name(rosdistro_name, source_build_name)
    return '%s__%s__%s_%s_%s' % \
           (view_name, repo_name, os_name, os_code_name, arch)


def configure_devel_view(jenkins, view_name):
    return configure_view(
        jenkins, view_name, include_regex='%s__.+' % view_name)


def _get_devel_job_config(
        config: SourceBuildConfiguration,
        os_arch_target: OSArchTarget,
        conf, source_repo_spec, repo_name):
    template_name = 'devel/devel_job.xml.em'
    now = datetime.utcnow()
    now_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    apt_mirror_args, script_generating_key_files = \
        get_apt_mirrors_and_script_generating_key_files(conf)

    job_data = {
        'template_name': template_name,
        'now_str': now_str,

        'job_priority': config.build_file.jenkins_job_priority,

        'source_repo_spec': source_repo_spec,

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_index_url': config.base.rosdistro_index_url,
        'rosdistro_name': config.base.rosdistro_name,
        'source_build_name': config.base.source_build_name,
        'os_name': os_arch_target.os_name,
        'os_code_name': os_arch_target.os_code_name,
        'arch': os_arch_target.arch,
        'apt_mirror_args': apt_mirror_args,

        'ros_buildfarm_url': get_ros_buildfarm_url(),

        'notify_emails': config.build_file.notify_emails,
        'maintainer_emails': config.get_maintainer_emails_to_notify(repo_name),
        'notify_maintainers': config.build_file.notify_maintainers,
        'notify_committers': config.build_file.notify_committers,

        'timeout_minutes': config.build_file.jenkins_job_timeout,
    }
    job_config = expand_template(template_name, job_data)
    return job_config
